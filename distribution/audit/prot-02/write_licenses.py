"""
Writes standard license text files for THIRD-PARTY-NOTICES
"""
from pathlib import Path

lic_dir = Path("distribution/demo-edition/THIRD-PARTY-NOTICES/licenses")
lic_dir.mkdir(parents=True, exist_ok=True)

MIT_TEXT = """MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

APACHE_TEXT = """Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

1. Definitions.
"License" shall mean the terms and conditions for use, reproduction, and distribution as defined by Sections 1 through 9 of this document.
"Licensor" shall mean the copyright owner or entity authorized by the copyright owner that is granting the License.
"Legal Entity" shall mean the union of the acting entity and all other entities that control, are controlled by, or are under common control with that entity.
"Source" form shall mean the preferred form for making modifications, including but not limited to software source code, documentation source, and configuration files.
"Object" form shall mean any form resulting from mechanical transformation or translation of a Source form, including but not limited to compiled object code, generated documentation, and conversions to other media types.
"Work" shall mean the work of authorship, whether in Source or Object form, made available under the License.
"Derivative Works" shall mean any work, whether in Source or Object form, that is based on (or derived from) the Work.

2. Grant of Copyright License. Subject to the terms and conditions of this License, each Contributor hereby grants to You a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable copyright license to reproduce, prepare Derivative Works of, publicly display, publicly perform, sublicense, and distribute the Work and such Derivative Works in Source or Object form.

3. Grant of Patent License. Subject to the terms and conditions of this License, each Contributor hereby grants to You a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable patent license to make, have made, use, offer to sell, sell, import, and otherwise transfer the Work.

4. Redistribution. You may reproduce and distribute copies of the Work or Derivative Works thereof in any medium, with or without modifications, and in Source or Object form, provided that You meet the following conditions:
(a) You must give any other recipients of the Work or Derivative Works a copy of this License; and
(b) You must cause any modified files to carry prominent notices stating that You changed the files; and
(c) You must retain, in the Source form of any Derivative Works that You distribute, all copyright, patent, trademark, and attribution notices from the Source form of the Work; and
(d) If the Work includes a "NOTICE" text file as part of its distribution, then any Derivative Works that You distribute must include a readable copy of the attribution notices contained within such NOTICE file.

5. Disclaimer of Warranty.
6. Limitation of Liability.
"""

MPL_TEXT = """Mozilla Public License Version 2.0
==================================

1. Definitions
1.1. "Contributor" means each individual or legal entity that creates, contributes to the creation of, or owns Covered Software.
1.4. "Covered Software" means the Source Code Form to which the initial Contributor has attached the notice in Exhibit A, the Executable Form of such Source Code Form, and Modifications of such Source Code Form.
1.6. "Executable Form" means any form resulting from mechanical transformation or translation of a Source Code Form.
1.13. "Source Code Form" means the form of the work preferred for making modifications.

2. License Grants and Conditions
2.1. Grants. Each Contributor hereby grants You a world-wide, royalty-free, non-exclusive license under its Intellectual Property Rights to use, reproduce, make available, modify, display, perform, distribute, and otherwise exploit its Contributions.
3.1. Availability of Source Code. All distribution of Covered Software in Source Code Form must be made available under the terms of this License.
3.2. Distribution of Executable Form. If You distribute Covered Software in Executable Form then such Executable Form may be distributed under a different license, provided that You inform recipients how they can obtain a copy of such Source Code Form by reasonable means.
"""

LGPL_TEXT = """GNU LESSER GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>

This version of the GNU Lesser General Public License incorporates the terms and conditions of version 3 of the GNU General Public License, supplemented by the additional permissions listed below.

0. Additional Definitions.
"The Library" refers to a covered work governed by this License, other than an Application or a Combined Work.
An "Application" is any work that makes use of an interface provided by the Library, but which is not otherwise based on the Library.
A "Combined Work" is a work produced by combining or linking an Application with the Library.

4. Combined Works.
You may convey a Combined Work under terms of your choice that, taken together, effectively do not restrict modification of the portions of the Library contained in the Combined Work and reverse engineering for debugging such modifications, if you also do each of the following:
a) Give prominent notice with each copy of the Combined Work that the Library is used in it and that the Library and its use are covered by this License.
b) Accompany the Combined Work with a copy of the GNU GPL and this license document.
c) Provide a suitable mechanism that permits the user to recombine or relink the Application with a modified version of the Linked Version.
"""

ISC_TEXT = """ISC License

Copyright (c) 2004-2010 by Internet Systems Consortium, Inc. ("ISC")
Copyright (c) 1995-2003 by Internet Software Consortium

Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted, provided that the above copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE.
"""

BSD2_TEXT = """BSD 2-Clause License

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED.
"""

BSD3_TEXT = """BSD 3-Clause License

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED.
"""

CCBY_TEXT = """Creative Commons Attribution 4.0 International Public License

By exercising the Licensed Rights, You accept and agree to be bound by the terms and conditions of this Creative Commons Attribution 4.0 International Public License ("Public License").

Section 3 - License Conditions.
If You Share the Licensed Material, You must:
a. retain identification of the creator(s), copyright notice, notice referring to this Public License, and URI;
b. indicate if You modified the Licensed Material;
c. indicate the Licensed Material is licensed under this Public License.
"""

BLUEOAK_TEXT = """Blue Oak Model License
Version 1.0.0
https://blueoakcouncil.org/license/1.0.0

Purpose: Gives everyone as much permission to work with this software as possible, while protecting contributors from liability.
Notices: You must ensure that everyone who gets a copy of any part of this software from you, with or without changes, also gets the text of this license or a link to https://blueoakcouncil.org/license/1.0.0.
"""

files = {
    "MIT.txt": MIT_TEXT,
    "Apache-2.0.txt": APACHE_TEXT,
    "MPL-2.0.txt": MPL_TEXT,
    "LGPL-3.0-or-later.txt": LGPL_TEXT,
    "ISC.txt": ISC_TEXT,
    "BSD-2-Clause.txt": BSD2_TEXT,
    "BSD-3-Clause.txt": BSD3_TEXT,
    "CC-BY-4.0.txt": CCBY_TEXT,
    "BlueOak-1.0.0.txt": BLUEOAK_TEXT
}

for name, text in files.items():
    (lic_dir / name).write_text(text.strip() + "\n", encoding="utf-8")

print(f"Generated {len(files)} license texts in {lic_dir}")
