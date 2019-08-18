# pydumpanalyzer

This project is a bit rough around the edges at this point.

PyDumpAnalyzer is a crash report server. It can take in/manage executable files, symbol files, and crash dump files via a REST/HTTP Flask app. The app also provides a rough interface for use via web browsers.

After a crash dump / symbols / executable are uploaded, the dump can be analyzed by the debugger to provide a call stack and a high level analysis. Of course if you need more info, the exported Windows symbol server can be used along with re-downloading the dump to further investigate locally in your debugger of choice.

Only supports C/C++ Windows at this point though could be expanded to Linux and more one day.

Right now there isn't much documentation other than the code itself. Though it could be added one day.

This project is licensed via the MIT License.