import { useState } from "react";

import {
    analyzeImage,
    generateDocument,
    downloadDocument
} from "./api";

import "./App.css";


function App() {

    const [file, setFile] = useState(null);

    const [result, setResult] = useState(null);

    const [format, setFormat] = useState("xlsx");

    const [status, setStatus] = useState("");

    const [loading, setLoading] = useState(false);


    async function handleAnalysis() {

        if (!file) return;

        setLoading(true);

        setStatus("Analysing document...");

        setResult(null);

        try {

            const data = await analyzeImage(file);

            setResult(data);

            setFormat(data.recommended_format);

            setStatus(
                `Analysis completed in ${data.processing_time}s`
            );

        } catch (error) {

            setStatus(error.message);

        } finally {

            setLoading(false);

        }

    }


    async function handleGeneration() {

        setLoading(true);

        setStatus("Generating document...");

        try {

            const generated = await generateDocument(
                result.job_id,
                format
            );

            await downloadDocument(
                result.job_id,
                format
            );

            setStatus(
                "Document generated successfully."
            );

        } catch (error) {

            setStatus(error.message);

        } finally {

            setLoading(false);

        }

    }


    return (

        <div className="app">

            <header>

                <h1>Document Reconstruction</h1>

                <p>
                    Convert document images into editable files.
                </p>

            </header>


            <section className="panel">

                <h2>Upload document</h2>

                <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={(e) =>
                        setFile(e.target.files[0])
                    }
                />

                {file && (
                    <p>{file.name}</p>
                )}

                <button
                    disabled={!file || loading}
                    onClick={handleAnalysis}
                >
                    {loading ? "Processing..." : "Analyse Document"}
                </button>

            </section>


            {result && (

                <section className="panel">

                    <h2>Analysis Results</h2>

                    <p>
                        Processing time:
                        {result.processing_time}s
                    </p>

                    <p>
                        Recommended format:
                        <strong>
                            {result.recommended_format.toUpperCase()}
                        </strong>
                    </p>


                    <div className="summary">

                        {[
                            "heading",
                            "paragraph",
                            "table",
                            "profile",
                            "list"
                        ].map(type => (

                            <div key={type}>

                                <strong>
                                    {
                                        result.elements.filter(
                                            e => e.type === type
                                        ).length
                                    }
                                </strong>

                                <span>{type}s</span>

                            </div>

                        ))}

                    </div>


                    <h3>Select output format</h3>

                    <select
                        value={format}
                        onChange={(e) =>
                            setFormat(e.target.value)
                        }
                    >

                        <option value="docx">
                            Word (.docx)
                        </option>

                        <option value="xlsx">
                            Excel (.xlsx)
                        </option>

                    </select>


                    {result.warnings?.length > 0 && (

                        <div className="warnings">

                            <h3>Review required</h3>

                            {result.warnings.map(
                                (warning, index) => (
                                    <p key={index}>
                                        {warning}
                                    </p>
                                )
                            )}

                        </div>

                    )}


                    <button
                        disabled={loading}
                        onClick={handleGeneration}
                    >
                        Generate and Download
                    </button>

                </section>

            )}


            {status && (

                <div className="status">
                    {status}
                </div>

            )}

        </div>

    );

}


export default App;