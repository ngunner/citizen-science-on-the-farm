# Run logs for `reproduce_disparity_pointmethod.py --zoom 12`

One console log per year (July 2026). Each ends with the year's summary block and the line
`saved -> …/outputs/pointmethod_<year>_z12_RESULT.csv`, **except 2023**: that log captures the first
2023 attempt, which crashed at the final concatenation because its checkpoint directory was inside the
cloud-synced project folder and the sync client removed files mid-run ("No objects to concatenate").
The run was repeated with checkpoints on local disk (`~/.csotf_pointmethod_ckpt/`, now the script's
default), producing `outputs/pointmethod_2023_z12_RESULT.csv` (disparity 3.2538; 150,410,082
observations); the console output of that successful re-run was not captured to a file.
Absolute home-directory paths in the logs were replaced with `~` / `<project>` at packaging.
