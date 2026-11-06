const API = "http://localhost:8000/api";


export async function analyzeImage(file) {

    const formData = new FormData();

    formData.append("file", file);

    const response = await fetch(
        `${API}/analyze`,
        {
            method: "POST",
            body: formData
        }
    );

    if (!response.ok) {

        const error = await response.json();

        throw new Error(
            error.detail || "Analysis failed"
        );
    }

    return response.json();
}


export async function generateDocument(
    jobId,
    format
) {

    const formData = new FormData();

    formData.append(
        "output_format",
        format
    );

    const response = await fetch(
        `${API}/generate/${jobId}`,
        {
            method: "POST",
            body: formData
        }
    );

    if (!response.ok) {

        throw new Error(
            "Document generation failed"
        );
    }

    return response.json();
}


export async function downloadDocument(
    jobId,
    format
) {

    const response = await fetch(
        `${API}/download/${jobId}/${format}`
    );

    if (!response.ok) {

        throw new Error(
            "Download failed"
        );
    }

    const blob = await response.blob();

    const url = window.URL.createObjectURL(blob);

    const link = document.createElement("a");

    link.href = url;

    link.download = `reconstructed_document.${format}`;

    link.click();

    window.URL.revokeObjectURL(url);
}