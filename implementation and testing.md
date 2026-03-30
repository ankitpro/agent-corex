

## Install venv
```
python -m venv .venv
```

## activate venv
```
.\.venv\Scripts\Activate.ps1 
```

## Install requirements
```
pip install -r requirements.txt
```

## If using google colab for ollama server then update the ollama url in .env file
```
OLLAMA_URL="https://mxczg-34-23-12-1.a.free.pinggy.link"
```


## Start the server
```
uvicorn apps.api.main:app --reload
```

## Test the tools loaded
```
http://localhost:8000/tools
```

### Expected output:
```
["filesystem"]
```

## Test tool retrieval
```
http://localhost:8000/retrieve_tools?query=commit code to github
```

### Expected response
```
[
  {"name": "git", "description": "Git operations like commit, push, pull"},
  {"name": "filesystem", "description": "Read/write local files"}
]
```

## Test endpoints with Swagger
```
http://localhost:8000/docs
```

## Inspect the tools installed using cli
```
python -m apps.cli.main inspect  
```