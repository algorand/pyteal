#!/usr/bin/env python3
"""
Helper functions and classes
"""

import subprocess
   
label_count = 0

def reset_label_count():
    global label_count
    label_count = 0

def new_label():
    global label_count
    new_l = "l{}".format(label_count)
    label_count += 1
    return new_l

def execute(args):
    """ Execute in bash, return stdout and stderr in string
    
    Arguments:
    args: command and arguments to run, e.g. ['ls', '-l']
    """
    process = subprocess.Popen(args, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    return (stdout.decode("utf-8"), stderr.decode("utf-8"))
