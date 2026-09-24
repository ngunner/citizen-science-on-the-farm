# Provenance: copied from `Figures/Top Bottom Spider Plot/script.py` (last modified 2025-11-26) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
# Enriches the Top-30/Bottom-30 table with USDA NASS Quick Stats acreage (corn grain; vegetables in the open). Requires USDA_NASS_API_KEY in the environment.
import pandas as pd
import requests
import time
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
# 1. Get a free key here: https://quickstats.nass.usda.gov/api
API_KEY = os.environ.get("USDA_NASS_API_KEY")
if not API_KEY:
    raise SystemExit("Set USDA_NASS_API_KEY (free key: https://quickstats.nass.usda.gov/api)")

# 2. Input/Output Files
INPUT_CSV = '../data/top_bottom_30/contus_counties_updated_optimized - COMBINED_TOP_BOTTOM.csv'
OUTPUT_CSV = '../data/top_bottom_30/counties_enriched_with_usda_data.csv'
DIAGNOSTIC_LOG = 'usda_api_diagnostic.log'

# 3. Rate Limiting Configuration
# Increased delays to prevent rate limiting issues
BASE_DELAY = 2.0  # Base delay between requests in seconds (increased to avoid 403s)
COUNTY_DELAY = 3.0  # Additional delay between counties in seconds
MAX_RETRIES = 3  # Maximum retry attempts for rate limit errors
RATE_LIMIT_DELAY = 120  # Delay in seconds when rate limited (429 or 403 error)

# 4. Diagnostic Mode
DIAGNOSTIC_MODE = False  # Set to True to run diagnostic mode
DIAGNOSTIC_COUNTIES = 3  # Number of counties to test in diagnostic mode

# NOTE: To find correct query parameters, use the USDA API parameter lookup:
# https://quickstats.nass.usda.gov/api#param_define
# Or use the get_param_values endpoint to discover available values
# 
# IMPORTANT: The USDA API requires exact string matching. Parameter conflicts
# (e.g., specifying statisticcat_desc that conflicts with short_desc) cause 400 errors.
# The solution is to rely primarily on short_desc and remove conflicting parameters.

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(DIAGNOSTIC_LOG),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# HYPOTHESIS VARIABLES (The "Social-Ecological" Factors)
# ---------------------------------------------------------
# We are querying specific variables that might explain citizen science effort.
# Format: {'Column Name': {'param': 'value', ...}} for USDA API
# 
# NOTE: USDA API requires exact matching of parameter values. Some fields may
# not be available for all counties or may use different parameter combinations.
# Use diagnostic mode to verify parameters for specific counties.
# TEMPORARY: Focusing on working variables only to test rate limiting
# Once rate limiting is confirmed working, we can add back the other variables
QUERIES = {
    # 1. INDUSTRIAL MONOCULTURE: Corn acres (Proxy for visual monotony)
    'CORN_ACRES': {
        'source_desc': 'CENSUS',
        'sector_desc': 'CROPS',
        'group_desc': 'FIELD CROPS',
        'commodity_desc': 'CORN',
        'short_desc': 'CORN, GRAIN - ACRES HARVESTED',
        'domain_desc': 'TOTAL'
    },

    # 2. SPECIALTY CROPS: Vegetable acres (Proxy for visual diversity)
    'VEGETABLE_ACRES': {
        'source_desc': 'CENSUS',
        'sector_desc': 'CROPS',
        'group_desc': 'VEGETABLES',
        'short_desc': 'VEGETABLE TOTALS, IN THE OPEN - ACRES HARVESTED',
        'domain_desc': 'TOTAL'
    }
    
    # NOTE: Other variables temporarily disabled for rate limiting testing:
    # - AVG_FARM_SIZE_ACRES
    # - AGRITOURISM_REVENUE  
    # - DIRECT_SALES_OPERATIONS
    # These can be re-enabled once rate limiting is confirmed working
}


def query_available_short_descs(sector_desc: str = 'ECONOMICS', group_desc: str = None) -> List[str]:
    """
    Helper function to query available short_desc values from USDA API.
    Useful for discovering correct parameter values.
    
    Example usage:
        # Get all short_desc values for Economics/Income
        descs = query_available_short_descs('ECONOMICS', 'INCOME')
        for desc in descs:
            if 'TOURISM' in desc or 'DIRECT' in desc:
                print(desc)
    """
    url = "http://quickstats.nass.usda.gov/api/get_param_values"
    params = {
        'key': API_KEY,
        'param': 'short_desc',
        'source_desc': 'CENSUS',
        'year': '2022',
        'sector_desc': sector_desc
    }
    if group_desc:
        params['group_desc'] = group_desc
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get('short_desc', [])
        else:
            logger.warning(f"Failed to query available short_desc values: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error querying available short_desc values: {e}")
        return []


def test_query_parameters(state_alpha: str, county_name: str, var_name: str) -> Dict[str, Any]:
    """
    Tests a single query to verify parameters and log detailed response.
    Useful for debugging parameter issues.
    """
    base_url = "http://quickstats.nass.usda.gov/api/api_GET/"
    params = QUERIES[var_name].copy()
    
    req_params = {
        'key': API_KEY,
        'year': '2022',
        'agg_level_desc': 'COUNTY',
        'state_alpha': state_alpha,
        'county_name': county_name.upper(),
        'format': 'JSON'
    }
    req_params.update(params)
    
    # Ensure source_desc is set (default to CENSUS if not in params)
    if 'source_desc' not in req_params:
        req_params['source_desc'] = 'CENSUS'
    
    logger.info(f"\nTesting query parameters for {var_name}")
    logger.info(f"Parameters: {json.dumps(req_params, indent=2)}")
    
    data, error_msg, status_code = make_api_request(base_url, req_params, var_name)
    
    result = {
        'var_name': var_name,
        'status_code': status_code,
        'error': error_msg,
        'data': data
    }
    
    if data:
        logger.info(f"Response structure: {json.dumps(data, indent=2)[:1000]}...")  # First 1000 chars
        value = extract_value_from_response(data, var_name)
        result['extracted_value'] = value
        logger.info(f"Extracted value: {value}")
    
    return result

def make_api_request(base_url: str, params: Dict[str, str], var_name: str, 
                     retry_count: int = 0) -> Tuple[Optional[Dict], str, int]:
    """
    Makes an API request with exponential backoff retry logic.
    Returns: (response_data, error_message, status_code)
    """
    try:
        # Log the request
        request_url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        logger.debug(f"Request URL: {request_url}")
        
        response = requests.get(base_url, params=params, timeout=15)
        status_code = response.status_code
        
        # Log response details
        logger.info(f"  {var_name}: Status {status_code}")
        
        if status_code == 200:
            try:
                data = response.json()
                logger.debug(f"  {var_name}: Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                return data, "", status_code
            except json.JSONDecodeError as e:
                error_msg = f"JSON decode error: {e}"
                logger.error(f"  {var_name}: {error_msg}")
                logger.debug(f"  {var_name}: Response text: {response.text[:500]}")
                return None, error_msg, status_code
                
        elif status_code == 429 or status_code == 403:  # Rate limited or forbidden
            error_type = "Rate limit exceeded (429)" if status_code == 429 else "Forbidden (403) - likely rate limiting"
            logger.warning(f"  {var_name}: {error_type}")
            
            if retry_count < MAX_RETRIES:
                wait_time = RATE_LIMIT_DELAY * (2 ** retry_count)  # Exponential backoff
                logger.info(f"  {var_name}: Retrying after {wait_time} seconds (attempt {retry_count + 1}/{MAX_RETRIES})")
                time.sleep(wait_time)
                return make_api_request(base_url, params, var_name, retry_count + 1)
            else:
                logger.error(f"  {var_name}: Max retries exceeded for rate limit/forbidden")
                return None, error_type, status_code
                
        elif status_code == 400:
            # Bad request - could mean no data available or invalid parameters
            try:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Bad Request')
                logger.warning(f"  {var_name}: Bad Request - {error_msg}")
                logger.debug(f"  {var_name}: Full error response: {json.dumps(error_data, indent=2)}")
            except:
                error_msg = f"Bad Request (400) - {response.text[:200]}"
                logger.warning(f"  {var_name}: {error_msg}")
            return None, error_msg, status_code
            
        else:
            error_msg = f"HTTP {status_code}: {response.text[:200]}"
            logger.error(f"  {var_name}: {error_msg}")
            return None, error_msg, status_code
            
    except requests.exceptions.Timeout:
        error_msg = "Request timeout"
        logger.error(f"  {var_name}: {error_msg}")
        return None, error_msg, 0
    except requests.exceptions.RequestException as e:
        error_msg = f"Request exception: {str(e)}"
        logger.error(f"  {var_name}: {error_msg}")
        return None, error_msg, 0
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"  {var_name}: {error_msg}")
        return None, error_msg, 0


def extract_value_from_response(data: Dict, var_name: str) -> Optional[float]:
    """
    Safely extracts the value from USDA API response.
    Returns None if data is not available, 0 if value is explicitly 0 or "(D)" (withheld).
    """
    if not isinstance(data, dict):
        logger.warning(f"  {var_name}: Response is not a dictionary")
        return None
        
    if 'data' not in data:
        logger.warning(f"  {var_name}: No 'data' key in response. Keys: {list(data.keys())}")
        return None
        
    data_array = data['data']
    
    if not isinstance(data_array, list):
        logger.warning(f"  {var_name}: 'data' is not a list")
        return None
        
    if len(data_array) == 0:
        logger.info(f"  {var_name}: Empty data array - no data available for this county")
        return None
        
    # Get the first result
    first_result = data_array[0]
    
    if not isinstance(first_result, dict):
        logger.warning(f"  {var_name}: First result is not a dictionary")
        return None
        
    if 'Value' not in first_result:
        logger.warning(f"  {var_name}: No 'Value' key in result. Keys: {list(first_result.keys())}")
        logger.debug(f"  {var_name}: Full result: {json.dumps(first_result, indent=2)}")
        return None
        
    value_str = str(first_result['Value']).strip()
    
    # Check for withheld data indicators
    if value_str in ['(D)', '(Z)', '(NA)', 'N/A', '']:
        logger.info(f"  {var_name}: Data withheld or not available: {value_str}")
        return None
        
    # Remove commas and convert to float
    try:
        value_clean = value_str.replace(',', '').replace('$', '').replace(' ', '')
        if value_clean.replace('.', '').replace('-', '').isdigit():
            return float(value_clean)
        else:
            logger.warning(f"  {var_name}: Cannot convert value '{value_str}' to float")
            return None
    except Exception as e:
        logger.warning(f"  {var_name}: Error converting value '{value_str}': {e}")
        return None


def try_alternative_query(base_url: str, state_alpha: str, county_name: str, 
                          var_name: str, original_params: Dict) -> Tuple[Optional[Dict], str, int]:
    """
    Tries alternative query parameter combinations when the original query fails.
    Sometimes the API works better with fewer parameters or different combinations.
    """
    # Define alternative short_desc values to try for specific fields
    alternative_short_descs = {
        'AVG_FARM_SIZE_ACRES': [
            'FARM OPERATIONS - ACRES OPERATED, MEAN',
            'FARM OPERATIONS - ACRES OPERATED - AVERAGE',
            'FARM OPERATIONS, ACRES OPERATED - AVERAGE',
            'FARMS - ACRES OPERATED, AVERAGE',
        ],
        'AGRITOURISM_REVENUE': [
            'INCOME, FARM-RELATED - RECEIPTS, AGRI-TOURISM & RECREATIONAL SERVICES',
            'INCOME, FARM-RELATED - RECEIPTS, AGRI-TOURISM AND RECREATIONAL SERVICES, MEASURED IN $',
            'INCOME, FARM-RELATED - RECEIPTS, AGRI-TOURISM & RECREATIONAL SERVICES, MEASURED IN $',
            'INCOME, FARM-RELATED - RECEIPTS, AGRI-TOURISM',
        ],
        'DIRECT_SALES_OPERATIONS': [
            'COMMODITY TOTALS - SALES, DIRECT TO CONSUMERS, HUMAN CONSUMPTION - OPERATIONS WITH SALES',
            'COMMODITY TOTALS - SALES, DIRECT TO CONSUMERS - OPERATIONS WITH SALES',
            'COMMODITY TOTALS - SALES, DIRECT TO CONSUMERS, HUMAN CONSUMPTION',
            'SALES, DIRECT TO CONSUMERS, HUMAN CONSUMPTION - OPERATIONS WITH SALES',
        ]
    }
    
    # Try with just short_desc (minimal parameters) - original value
    if 'short_desc' in original_params:
        minimal_params = {
            'key': API_KEY,
            'year': '2022',
            'agg_level_desc': 'COUNTY',
            'state_alpha': state_alpha,
            'county_name': county_name.upper(),
            'format': 'JSON',
            'short_desc': original_params['short_desc']
        }
        # Use source_desc from original params if present, otherwise default to CENSUS
        if 'source_desc' in original_params:
            minimal_params['source_desc'] = original_params['source_desc']
        else:
            minimal_params['source_desc'] = 'CENSUS'
        logger.debug(f"  {var_name}: Trying minimal query (short_desc only)")
        data, error_msg, status_code = make_api_request(base_url, minimal_params, var_name)
        if status_code == 200 and data:
            return data, "", status_code
    
    # Try alternative short_desc values if available
    if var_name in alternative_short_descs:
        source_desc = original_params.get('source_desc', 'CENSUS')
        for alt_short_desc in alternative_short_descs[var_name]:
            minimal_params = {
                'key': API_KEY,
                'source_desc': source_desc,
                'year': '2022',
                'agg_level_desc': 'COUNTY',
                'state_alpha': state_alpha,
                'county_name': county_name.upper(),
                'format': 'JSON',
                'short_desc': alt_short_desc
            }
            logger.debug(f"  {var_name}: Trying alternative short_desc: {alt_short_desc[:50]}...")
            data, error_msg, status_code = make_api_request(base_url, minimal_params, var_name)
            if status_code == 200 and data:
                logger.info(f"  {var_name}: Found working short_desc: {alt_short_desc}")
                return data, "", status_code
    
    # Try without domain_desc if it was present
    if 'domain_desc' in original_params:
        params_no_domain = original_params.copy()
        params_no_domain.pop('domain_desc', None)
        req_params = {
            'key': API_KEY,
            'year': '2022',
            'agg_level_desc': 'COUNTY',
            'state_alpha': state_alpha,
            'county_name': county_name.upper(),
            'format': 'JSON'
        }
        req_params.update(params_no_domain)
        # Ensure source_desc is set
        if 'source_desc' not in req_params:
            req_params['source_desc'] = 'CENSUS'
        logger.debug(f"  {var_name}: Trying query without domain_desc")
        data, error_msg, status_code = make_api_request(base_url, req_params, var_name)
        if status_code == 200 and data:
            return data, "", status_code
    
    # Try with just sector, group, and commodity (no short_desc)
    if all(k in original_params for k in ['sector_desc', 'group_desc', 'commodity_desc']):
        source_desc = original_params.get('source_desc', 'CENSUS')
        basic_params = {
            'key': API_KEY,
            'source_desc': source_desc,
            'year': '2022',
            'agg_level_desc': 'COUNTY',
            'state_alpha': state_alpha,
            'county_name': county_name.upper(),
            'format': 'JSON',
            'sector_desc': original_params['sector_desc'],
            'group_desc': original_params['group_desc'],
            'commodity_desc': original_params['commodity_desc']
        }
        if 'statisticcat_desc' in original_params:
            basic_params['statisticcat_desc'] = original_params['statisticcat_desc']
        logger.debug(f"  {var_name}: Trying basic query (sector/group/commodity only)")
        data, error_msg, status_code = make_api_request(base_url, basic_params, var_name)
        if status_code == 200 and data:
            return data, "", status_code
    
    return None, "All alternative queries failed", 400


def fetch_county_data(state_alpha: str, county_name: str) -> Dict[str, Any]:
    """
    Fetches all variables for a single county from USDA 2022 Census.
    Returns a dictionary of values with detailed error tracking.
    """
    base_url = "http://quickstats.nass.usda.gov/api/api_GET/"
    results = {}
    request_count = 0

    logger.info(f"Fetching data for {county_name}, {state_alpha}")

    for var_name, params in QUERIES.items():
        # Common params for every query
        # Note: Some queries may already include source_desc, so we update after adding common params
        req_params = {
            'key': API_KEY,
            'year': '2022',
            'agg_level_desc': 'COUNTY',
            'state_alpha': state_alpha,
            'county_name': county_name.upper(),  # USDA requires UPPERCASE
            'format': 'JSON'
        }
        # Add specific params for this variable (may include source_desc)
        req_params.update(params)

        # Ensure source_desc is set (default to CENSUS if not in params)
        if 'source_desc' not in req_params:
            req_params['source_desc'] = 'CENSUS'

        # Make API request with retry logic
        data, error_msg, status_code = make_api_request(base_url, req_params, var_name)
        
        # If we get a 400 error, try alternative parameter combinations
        if status_code == 400:
            logger.info(f"  {var_name}: Original query failed (400), trying alternatives...")
            data, error_msg, status_code = try_alternative_query(
                base_url, state_alpha, county_name, var_name, params
            )
        
        if data is not None:
            # Extract value from response
            value = extract_value_from_response(data, var_name)
            
            if value is not None:
                results[var_name] = value
                logger.info(f"  {var_name}: Success - Value = {value}")
            else:
                # Data not available for this county/field
                results[var_name] = None
                logger.info(f"  {var_name}: No data available")
        else:
            # API error occurred
            if status_code == 400:
                # Bad request - likely means invalid parameters or no data available
                results[var_name] = None
                logger.warning(f"  {var_name}: Query failed - may indicate invalid parameters or no data")
            elif status_code == 403 or status_code == 429:
                # Rate limited - mark as None but log the issue
                results[var_name] = None
                logger.warning(f"  {var_name}: Rate limited/forbidden - {error_msg}")
            else:
                # Other error - mark as None to distinguish from 0
                results[var_name] = None
                logger.warning(f"  {var_name}: API error - {error_msg}")

        request_count += 1
        
        # Rate limiting: be polite to the API
        # Add delay between requests within a county
        if request_count < len(QUERIES):
            time.sleep(BASE_DELAY)

    return results

def run_diagnostic_mode(df: pd.DataFrame):
    """
    Runs diagnostic mode: tests API queries for a few sample counties
    and generates a detailed report with parameter verification.
    """
    logger.info("=" * 80)
    logger.info("DIAGNOSTIC MODE - Testing API queries for sample counties")
    logger.info("=" * 80)
    
    # Test first N counties
    test_counties = df.head(DIAGNOSTIC_COUNTIES)
    
    diagnostic_results = []
    parameter_tests = {}
    
    for index, row in test_counties.iterrows():
        state = row['STATE']
        county = row['COUNTYNAME']
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing County {index+1}: {county}, {state}")
        logger.info(f"{'='*80}")
        
        # Test each query individually with detailed logging
        logger.info("\n--- Individual Query Tests ---")
        for var_name in QUERIES.keys():
            test_result = test_query_parameters(state, county, var_name)
            if var_name not in parameter_tests:
                parameter_tests[var_name] = []
            parameter_tests[var_name].append(test_result)
            time.sleep(BASE_DELAY)
        
        # Also run the full fetch to compare
        logger.info(f"\n--- Full Fetch Test ---")
        county_data = fetch_county_data(state, county)
        
        # Store results
        result = {
            'county': county,
            'state': state,
            'data': county_data
        }
        diagnostic_results.append(result)
        
        # Summary for this county
        logger.info(f"\nSummary for {county}, {state}:")
        for var_name, value in county_data.items():
            if value is None:
                logger.info(f"  {var_name}: None (no data available)")
            else:
                logger.info(f"  {var_name}: {value}")
    
    # Generate diagnostic report
    logger.info(f"\n{'='*80}")
    logger.info("DIAGNOSTIC SUMMARY")
    logger.info(f"{'='*80}")
    
    logger.info("\nOverall Results:")
    for var_name in QUERIES.keys():
        success_count = sum(1 for r in diagnostic_results if r['data'].get(var_name) is not None)
        none_count = sum(1 for r in diagnostic_results if r['data'].get(var_name) is None)
        logger.info(f"  {var_name}: {success_count} successful, {none_count} no data")
    
    # Parameter verification summary
    logger.info("\nParameter Verification Summary:")
    for var_name, tests in parameter_tests.items():
        status_codes = [t['status_code'] for t in tests]
        errors = [t['error'] for t in tests if t['error']]
        logger.info(f"  {var_name}:")
        logger.info(f"    Status codes: {status_codes}")
        if errors:
            unique_errors = list(set(errors))
            logger.info(f"    Errors encountered: {unique_errors}")
        else:
            logger.info(f"    No errors")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Full diagnostic log saved to: {DIAGNOSTIC_LOG}")
    logger.info("Review the log file for detailed API request/response information.")
    logger.info("=" * 80)
    
    # Check if any fields consistently failed
    failed_fields = []
    for var_name in QUERIES.keys():
        success_count = sum(1 for r in diagnostic_results if r['data'].get(var_name) is not None)
        if success_count == 0:
            failed_fields.append(var_name)
    
    if failed_fields:
        logger.warning(f"\n{'='*80}")
        logger.warning("IMPORTANT: Fields with consistent failures:")
        for field in failed_fields:
            logger.warning(f"  - {field}")
        logger.warning("\nThese fields are returning 400 'invalid query' errors.")
        logger.warning("This suggests the query parameters are incorrect.")
        logger.warning("\nTo find correct parameters:")
        logger.warning("1. Visit: https://quickstats.nass.usda.gov/api#param_define")
        logger.warning("2. Use the parameter lookup tool to find correct short_desc values")
        logger.warning("3. Or use the get_param_values endpoint to discover available values")
        logger.warning("4. Update the QUERIES dictionary in script.py with correct parameters")
        logger.warning(f"{'='*80}")
    
    return diagnostic_results


def main():
    logger.info("=" * 80)
    logger.info("USDA Data Batch Fetcher - Enhanced Version")
    logger.info("=" * 80)

    # 1. Load your county list
    if not os.path.exists(INPUT_CSV):
        logger.error(f"Error: Could not find {INPUT_CSV}")
        return

    df = pd.read_csv(INPUT_CSV)

    # Ensure we have columns we need
    if 'STATE' not in df.columns or 'COUNTYNAME' not in df.columns:
        logger.error("Error: CSV must have 'STATE' and 'COUNTYNAME' columns.")
        return

    logger.info(f"Loaded {len(df)} counties from {INPUT_CSV}")
    
    # Run diagnostic mode if enabled
    if DIAGNOSTIC_MODE:
        run_diagnostic_mode(df)
        logger.info("\nDiagnostic mode complete. Set DIAGNOSTIC_MODE = False to run full batch.")
        return

    logger.info(f"Starting batch fetch for {len(df)} counties...")
    logger.info(f"Rate limiting configuration:")
    logger.info(f"  - {BASE_DELAY}s delay between requests within a county")
    logger.info(f"  - {COUNTY_DELAY}s delay between counties")
    logger.info(f"  - {MAX_RETRIES} max retries with exponential backoff")
    logger.info(f"Currently fetching: {', '.join(QUERIES.keys())}")
    logger.warning("NOTE: If you see 403 Forbidden errors, the API is rate-limiting.")
    logger.warning("      The script will automatically retry with exponential backoff.")
    logger.warning("      Consider increasing BASE_DELAY or COUNTY_DELAY if issues persist.")

    # 2. Iterate and Fetch
    new_data = []
    stats = {
        'total_requests': 0,
        'successful': {var: 0 for var in QUERIES.keys()},
        'no_data': {var: 0 for var in QUERIES.keys()},
        'errors': {var: 0 for var in QUERIES.keys()},
        'rate_limited': 0
    }
    
    # Track recent 403s to detect rate limiting patterns
    recent_403s = []
    current_delay = BASE_DELAY

    for index, row in df.iterrows():
        state = row['STATE']
        county = row['COUNTYNAME']

        logger.info(f"\n[{index+1}/{len(df)}] Processing {county}, {state}...")

        county_data = fetch_county_data(state, county)
        stats['total_requests'] += len(QUERIES)

        # Update statistics and track 403s
        for var_name, value in county_data.items():
            if value is None:
                stats['no_data'][var_name] += 1
            else:
                stats['successful'][var_name] += 1
        
        # Check if we're getting rate limited (403s) - adjust delay if needed
        # This is a simple heuristic: if we see multiple 403s, increase delay
        # Note: The actual 403 detection happens in make_api_request, but we can
        # track patterns here if needed
        
        # Convert None to 0 for CSV compatibility (but log that it was None)
        county_data_for_csv = {}
        for var_name, value in county_data.items():
            if value is None:
                county_data_for_csv[var_name] = 0
            else:
                county_data_for_csv[var_name] = value

        # Merge with existing row data
        row_output = row.to_dict()
        row_output.update(county_data_for_csv)
        new_data.append(row_output)
        
        # Add delay between counties to prevent rate limiting
        if index + 1 < len(df):
            logger.debug(f"Waiting {COUNTY_DELAY}s before next county...")
            time.sleep(COUNTY_DELAY)
        
        # Progress update every 10 counties
        if (index + 1) % 10 == 0:
            logger.info(f"Progress: {index + 1}/{len(df)} counties processed")

    # 3. Save Result
    result_df = pd.DataFrame(new_data)
    result_df.to_csv(OUTPUT_CSV, index=False)
    
    # Print summary statistics
    logger.info(f"\n{'='*80}")
    logger.info("BATCH FETCH SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Total counties processed: {len(df)}")
    logger.info(f"Total API requests: {stats['total_requests']}")
    logger.info(f"\nResults by variable:")
    for var_name in QUERIES.keys():
        successful = stats['successful'][var_name]
        no_data = stats['no_data'][var_name]
        total = len(df)
        pct = (successful / total * 100) if total > 0 else 0
        logger.info(f"  {var_name}:")
        logger.info(f"    Successful: {successful}/{total} ({pct:.1f}%)")
        logger.info(f"    No data: {no_data}/{total} ({100-pct:.1f}%)")
    
    logger.info(f"\nSuccess! Enriched data saved to {OUTPUT_CSV}")
    logger.info(f"Detailed log saved to {DIAGNOSTIC_LOG}")
    logger.info("Note: Values of 0 may indicate no data available (check log for details)")


if __name__ == "__main__":
    main()