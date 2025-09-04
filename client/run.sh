#!/bin/bash

# Set environment variables
export EMBEDDING_MODEL="granite-embedding-125m"
export EMBEDDING_DIMENSION="768"
export EMBEDDING_MODEL_PROVIDER="sentence-transformers"
export LLAMA_STACK_HOST="localhost"
export LLAMA_STACK_PORT="8080"
export LLAMA_STACK_SECURE="False"
export DOCS_FOLDER="./docs"
export CHUNK_SIZE_IN_TOKENS="256"

# Run the script
python run.py