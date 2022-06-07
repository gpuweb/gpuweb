#!/usr/bin/env python3
# Extracts the text from the "IDL Index" section of a Bikeshed HTML file.
# Does so by first finding the "IDL Index" header <h2> element, then printing
# all the text inside the following <pre> element.

import argparse
from datetime import date
from html.parser import HTMLParser

HEADER = """
// Copyright (C) [{year}] World Wide Web Consortium,
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
""".lstrip().format(year=date.today().year)


class IDLIndexPrinter(HTMLParser):
    def __init__(self):
        super().__init__()
        # 0 = haven't found idl index yet
        # 1 = found idl index <h2> header
        # 2 = inside the <pre> block of the index
        # 3 = pre block ended
        self.search_state = 0

    def handle_starttag(self, tag, attrs):
        if self.search_state == 0:
            if tag == 'h2' and ('id', 'idl-index') in attrs:
                self.search_state = 1
        elif self.search_state == 1:
            if tag == 'pre':
                self.search_state = 2

    def handle_endtag(self, tag):
        if self.search_state == 2:
            if tag == 'pre':
                self.search_state = 3

    def handle_data(self, data):
        if self.search_state == 2:
            print(data, end='')


if __name__ == '__main__':
    args_parser = argparse.ArgumentParser(
        'Extract WebIDL from the HTML output of Bikeshed')
    args_parser.add_argument('htmlfile',
                             type=argparse.FileType('r'),
                             help='HTML output file from Bikeshed')
    args = args_parser.parse_args()

    print(HEADER)

    parse_and_print = IDLIndexPrinter()
    parse_and_print.feed(args.htmlfile.read())
