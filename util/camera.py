import subprocess


subprocess.check_output([
    'raspistill',
    '-n',  # No preview window.
    '-vf', # Vertical flip.
    '-hf', # Horizontal flip.
    '-o', 'test.jpg'  # Output file.
], stderr=subprocess.STDOUT)
