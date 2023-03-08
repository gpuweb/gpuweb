#!/usr/bin/env python3
#
# Copyright 2023 Google LLC
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of works must retain the original copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the original
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#
# 3. Neither the name of the W3C nor the names of its contributors
# may be used to endorse or promote products derived from this work
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from wgsl_unit_tests import Case, XFail, MatchCase

cases = [
    XFail("enable;"),
    Case("enable f16;"),

    # Demonstrate TSPath pattern matching
    MatchCase("enable f16;","//enable_directive","enable_directive:enable f16;"),
    MatchCase("enable f16;","//enable_directive/enable_extension_list","enable_extension_list:f16"), # child
    MatchCase("enable f16;","enable_extension_list//ident_pattern_token","ident_pattern_token:f16"),
    MatchCase("enable f16;","//enable_directive[0]","enable:enable"), # literal text in the rule
    MatchCase("enable f16;","//enable_directive[1]","enable_extension_list:f16"),
    MatchCase("enable f16;","//enable_directive[2]",";:;"), # literal text in the rule
    MatchCase("enable f16;","//enable_directive(0)","enable:enable"),
    MatchCase("enable f16;","//enable_directive(1)","enable_extension_list:f16"),
    MatchCase("enable f16;","//enable_directive(2)",";:;"),
    MatchCase("enable f16;","//enable_directive(0 1 2)","enable:enable enable_extension_list:f16 ;:;"),
]
