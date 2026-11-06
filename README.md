# DocRec --- Document Reconstruction

Turn document images into editable Word and Excel files.

DocRec is a document-reconstruction application designed to help people
reuse information locked inside screenshots, scanned pages, and other
document images. Upload an image, let the AI extract its content and
structure, review the result, and generate an editable **Word
(`.docx`)** or **Excel (`.xlsx`)** file.

> **Project status:** DocRec is under active development. Extraction
> quality depends on image clarity, layout complexity, the selected AI
> provider, model availability, and API limits. Always review generated
> files before using them.

------------------------------------------------------------------------

## Table of contents

-   [The idea](#the-idea)
-   [What DocRec does](#what-docrec-does)
-   [How it works](#how-it-works)
-   [Technology used](#technology-used)
-   [Requirements](#requirements)
-   [Run DocRec on your computer](#run-docrec-on-your-computer)
-   [Use the application](#use-the-application)
-   [AI provider configuration](#ai-provider-configuration)
-   [Project structure](#project-structure)
-   [Troubleshooting](#troubleshooting)
-   [Current limitations](#current-limitations)
-   [Contributing](#contributing)
-   [License](#license)

## The idea

A lot of useful information exists in images rather than editable
documents. For example:

-   A photograph of a printed table may need to become an Excel
    spreadsheet.
-   A screenshot of a job description may need to become a Word
    document.
-   A scanned page containing headings, paragraphs, lists, and tables
    may need to be edited or reused.

Typing all of this information again takes time. Basic OCR can recognize
text, but it may not understand how the text is organised.

DocRec aims to go a step further: it uses a vision-capable AI model to
read the image, identify the different content types, and reconstruct
them in an editable file.

## What DocRec does

1.  **Upload an image** --- provide a supported document image from your
    computer.
2.  **Extract content** --- the AI reads visible text, numbers, tables,
    lists, and other structures.
3.  **Organise the content** --- the backend validates the extracted
    data and classifies its elements.
4.  **Choose an output format** --- DocRec recommends Word or Excel
    based on the extracted content. Where the interface supports it,
    review or change the format.
5.  **Generate and download** --- create an editable `.docx` or `.xlsx`
    file.

The goal is to preserve the information and its logical structure.
DocRec does not currently promise a pixel-perfect copy of the original
page.

## How it works

``` text
User's browser
      |
      v
React + Vite frontend
      |
      v
FastAPI backend
      |
      v
Image preparation / optional region cropping
      |
      v
Groq vision model (primary)
      |
      | if the primary provider fails
      v
Ollama with a local vision model (fallback)
      |
      v
Structured JSON response
      |
      v
Pydantic validation and document classification
      |
      +---------------------+
      |                     |
      v                     v
Word generator         Excel generator
(python-docx)          (openpyxl)
      |                     |
      v                     v
Editable DOCX          Editable XLSX
```

The frontend communicates with the FastAPI backend. The backend sends
the image to the configured AI provider, validates the returned
structured data, and uses Python libraries to create the output file.

### Region-based extraction

For some image layouts, DocRec can split an image into smaller regions
before sending them for extraction. This can make dense regions easier
for a model to process and can reduce the size of an individual
response.

The current region settings are configurable. A fixed grid is not
suitable for every page, so region extraction should be tested against
the type of image being processed. Splitting an image does not eliminate
provider-wide token or request limits.

## Technology used

  -----------------------------------------------------------------------
  Software / service                  Purpose in DocRec
  ----------------------------------- -----------------------------------
  **Python 3.11**                     Backend programming language

  **FastAPI**                         Provides the backend API and
                                      upload, analysis, generation, and
                                      download endpoints

  **Uvicorn**                         Runs the FastAPI application

  **React**                           Builds the browser user interface

  **Vite**                            Frontend development server and
                                      build tooling

  **Docker**                          Packages application components
                                      into containers

  **Docker Compose**                  Starts and connects the frontend,
                                      backend, and Ollama services

  **Groq API**                        Primary hosted AI inference
                                      provider for image understanding
                                      and extraction

  **Ollama**                          Runs a vision-capable AI model
                                      locally as a fallback provider

  **Qwen2.5-VL 7B**                   Vision-language model configured
                                      for local image understanding
                                      through Ollama

  **Pydantic**                        Validates and normalises the
                                      structured data returned by the AI

  **Pillow**                          Opens, converts, and crops images
                                      for preprocessing and region
                                      extraction

  **python-docx**                     Creates editable Microsoft Word
                                      documents

  **openpyxl**                        Creates editable Microsoft Excel
                                      workbooks

  **python-multipart**                Handles file uploads in FastAPI

  **Git and GitHub**                  Version control and public
                                      source-code hosting
  -----------------------------------------------------------------------

The exact model name and provider settings are controlled by the
project's environment configuration. Model availability, API quotas, and
provider terms can change.

## Requirements

Before running DocRec, install:

-   Git
-   Docker Desktop (with Docker Compose)
-   A Groq API key if you want to use Groq as the primary provider
-   Sufficient disk space and memory for the Ollama model if you use the
    local fallback

You do not need to install the backend Python packages or frontend Node
packages directly when using the supplied Docker setup. Docker builds
the application containers from the project files.

## Run DocRec on your computer

### 1. Get the source code

Clone the repository:

``` bash
git clone https://github.com/YOUR_GITHUB_USERNAME/DocRec.git
cd DocRec
```

Replace `YOUR_GITHUB_USERNAME` with the GitHub account that hosts the
repository.

Alternatively, download the repository as a ZIP file from GitHub and
extract it.

### 2. Configure environment variables

Create the backend environment file from the example:

``` bash
cp backend/.env.example backend/.env
```

On Windows PowerShell, you can use:

``` powershell
Copy-Item backend/.env.example backend/.env
```

Open `backend/.env` and add your own Groq API key. For example:

``` env
AI_PROVIDER=groq
FALLBACK_PROVIDER=ollama

GROQ_API_KEY=replace_with_your_groq_api_key
GROQ_MODEL=your_supported_vision_model

OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=qwen2.5vl:7b
```

Use a vision-capable Groq model that is currently available to your
account and supported by the provider integration. Do not commit your
real `.env` file or API key to GitHub.

If your project uses additional environment variables for region
extraction, CORS, or token limits, copy those settings from the
project's current configuration and `.env.example`.

### 3. Start the application

From the project root, run:

``` bash
docker compose up -d --build
```

This builds and starts the services in the background.

Check their status:

``` bash
docker compose ps
```

View logs if a service does not start:

``` bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f ollama
```

### 4. Download the local Ollama model

If Ollama is enabled and the model has not already been downloaded, run:

``` bash
docker compose exec ollama ollama pull qwen2.5vl:7b
```

The model download can take time and requires sufficient disk space. The
named Docker volume used by the Compose configuration should retain the
downloaded model between container restarts.

### 5. Open DocRec

When the services are running, open:

  Component                   Local address
  --------------------------- ----------------------------
  DocRec frontend             http://localhost:5173
  Backend API documentation   http://localhost:8000/docs
  Ollama API                  http://localhost:11434

The frontend is the normal starting point for using the application. The
API documentation is useful for developers testing backend endpoints.

## Use the application

1.  Open **http://localhost:5173** in your browser.
2.  Select a document image from your computer.
3.  Start the analysis.
4.  Review the extracted text and structure shown by the application.
5.  Check the recommended output format.
6.  Generate the Word or Excel file.
7.  Download the generated file and open it in Microsoft Word, Excel, or
    a compatible office application.
8.  Check important names, numbers, table cells, and formatting against
    the source image.

AI extraction can make mistakes. Do not assume that a generated file is
correct without reviewing it.

## AI provider configuration

DocRec is designed to use two providers:

### Primary: Groq

Groq provides hosted model inference. The backend sends the image and
extraction instructions to the configured vision-capable model.

You must provide your own API key. Usage limits and model availability
depend on your Groq account and the provider's current policies.

### Fallback: Ollama

Ollama runs a model on the computer or server hosting the Ollama
container. The configured fallback model is `qwen2.5vl:7b`.

The model must be downloaded before it can be used. Local inference
depends on available RAM, CPU, and GPU resources. It may be slower than
hosted inference.

A local model does not mean unlimited computing capacity: hardware
resources and model licences still apply.

## Project structure

The repository is organised into frontend and backend components. The
exact files may change as development continues.

``` text
DocRec/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── schemas.py
│   │   ├── ai_extractor.py
│   │   ├── region_extractor.py
│   │   ├── classifier.py
│   │   ├── validator.py
│   │   ├── word_generator.py
│   │   ├── excel_generator.py
│   │   └── providers/
│   │       ├── extraction_manager.py
│   │       ├── groq_provider.py
│   │       └── ollama_provider.py
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── storage/
├── docker-compose.yml
├── .gitignore
└── README.md
```

Some projects keep the storage directories inside `backend/`. Follow the
actual directory layout in the repository if it differs from this
example.

## Troubleshooting

### The frontend opens, but analysis fails

Check the backend logs:

``` bash
docker compose logs -f backend
```

Confirm that the Groq API key, model name, and provider configuration
are correct.

### Groq returns a rate-limit error

The provider may have reached an input-token, output-token, request, or
time-based quota. Try again after the quota window resets, reduce the
amount of content requested per extraction, or use the configured Ollama
fallback. Region-based extraction can reduce the size of individual
responses but does not remove provider quotas.

### Ollama is not running

Check:

``` bash
docker compose ps
docker compose logs -f ollama
```

Start it if necessary:

``` bash
docker compose up -d ollama
```

Then pull the configured model:

``` bash
docker compose exec ollama ollama pull qwen2.5vl:7b
```

### Rebuild after changing backend or frontend code

``` bash
docker compose up -d --build
```

### Stop the application

``` bash
docker compose down
```

This stops the containers. Named volumes are normally retained unless
you explicitly remove them.

## Current limitations

DocRec is an evolving project. Current areas for improvement include:

-   Complex multi-column page layout reconstruction.
-   Accurate detection of table boundaries and multi-level headers.
-   Merged cells, diagrams, handwriting, and low-resolution images.
-   Reading order across columns and around embedded tables.
-   Automatic selection of the best region-cropping strategy.
-   Consistent extraction across different AI models.
-   Large documents and provider token/request limits.
-   Persistent job history and production-grade file storage, depending
    on the deployment configuration.

The current goal is to reconstruct useful, editable content. Exact
reproduction of the original page's visual appearance is not guaranteed.

## Contributing

Contributions, bug reports, and suggestions are welcome.

1.  Fork the repository.

2.  Create a branch for your change:

    ``` bash
    git checkout -b feature/your-change
    ```

3.  Make and test your changes.

4.  Commit your work:

    ``` bash
    git add .
    git commit -m "Describe your change"
    ```

5.  Push the branch:

    ``` bash
    git push origin feature/your-change
    ```

6.  Open a Pull Request on GitHub and explain what changed and how you
    tested it.

When reporting an extraction issue, include (where safe to share) the
type of source image, the expected result, the actual result, and the
error message. Never include API keys or private documents.

## License

No open-source licence has been selected in this repository yet. Until a
licence is added, others do not automatically have permission to reuse,
modify, or distribute the code. Choose and add a licence file before
presenting the project as open source.
