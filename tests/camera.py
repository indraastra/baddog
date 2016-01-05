import subprocess


subprocess.check_output([
    'raspistill',
    '-n',  # No preview window.
    '-vf', # Vertical flip.
    '-hf', # Horizontal flip.
    '-t', '1', # 1ms timeout.
    '-o', 'test.jpg'  # Output file.
], stderr=subprocess.STDOUT)
