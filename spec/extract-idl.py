#!/usr/bin/python

from datetime import date
from string import Template
import re
import sys

HEADER = """
// Copyright (C) [$YEAR] World Wide Web Consortium,
// (Massachusetts Institute of Technology, European Research Consortium for
// Informatics and Mathematics, Keio University, Beihang).
// All Rights Reserved.
//
// This work is distributed under the W3C (R) Software License [1] in the hope
// that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
// warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
//
// [1] http://www.w3.org/Consortium/Legal/copyright-software

// **** This file is auto-generated. Do not edit. ****

""".lstrip()

inputfilename = sys.argv[1]
inputfile = open(inputfilename)
idlList = []
recording = False
idlStart = re.compile("\<script .*type=[\'\"]?idl")
idlStop = re.compile("\</script\>")

idlLineList = []
for line in inputfile:
    line = line.rstrip()
    if idlStart.search(line) != None:
        recording = True
    elif idlStop.search(line) != None:
        recording = False
        idlList.append("\n".join(idlLineList))
        idlLineList = []
    elif recording:
        idlLineList.append(line)

headerTemplate = Template(HEADER)
print(headerTemplate.substitute(YEAR=date.today().year) + "\n\n\n".join(idlList))
