# pa.schema.yaml

`pa.schema.yaml` in this folder is the official Power Apps canvas-app source schema, version 3.0,
from Microsoft's [PowerApps-Tooling](https://github.com/microsoft/PowerApps-Tooling) repository
(path `schemas/pa-yaml/v3.0/pa.schema.yaml`). It is published under the MIT License, whose copyright
notice and permission notice are reproduced below as that licence requires.

Fetched 2026-09-26 from the `master` branch. **Unmodified**: the copy is byte-identical to the file
as published (584 lines, `$id: http://powerapps.com/schemas/pa-yaml/v3.0/pa.schema`). Do not edit it
here; replace it with a fresh copy and update this note when a newer schema version is adopted.

`tests/test_mobile_powerapp.py` reads the schema's control-type pattern and its disallowed-type
enumerations from this file, and a local check with `jsonschema` (Draft 7) validates the merged
`src/**/*.pa.yaml` against it; see `mobile/README.md`.

---

MIT License

Copyright (c) Microsoft Corporation.

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
