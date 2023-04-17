
entry_str = """webencodings, wcwidth, Send2Trash, pure-eval, ptyprocess, pickleshare, mistune, ipython-genutils, fastjsonschema, executing, backcall, appnope, widgetsnbextension, websocket-client, webcolors, uri-template, traitlets, tornado, tinycss2, soupsieve, sniffio, rfc3986-validator, rfc3339-validator, pyzmq, pyyaml, python-json-logger, python-dateutil, pyrsistent, pygments, pycparser, psutil, prompt-toolkit, prometheus-client, platformdirs, pexpect, parso, pandocfilters, packaging, nest-asyncio, markupsafe, jupyterlab-widgets, jupyterlab-pygments, jsonpointer, idna, fqdn, defusedxml, decorator, debugpy, bleach, attrs, asttokens, terminado, stack-data, qtpy, matplotlib-inline, jupyter-core, jsonschema, jinja2, jedi, comm, cffi, beautifulsoup4, arrow, anyio, nbformat, jupyter-server-terminals, jupyter-client, isoduration, ipython, argon2-cffi-bindings, nbclient, ipykernel, argon2-cffi, qtconsole, nbconvert, jupyter-events, jupyter-console, ipywidgets, jupyter-server, notebook-shim, nbclassic, notebook, jupyter"""

entries = map(lambda x: f'"{x.strip()}"', entry_str.split(","))

print(' '.join(entries))
