import functions_framework
import os
import logging
from flask import jsonify
import vertexai
from vertexai.generative_models import GenerativeModel, Part

@functions_framework.http
def transcripts(request):
    """
    HTTP Cloud Function to process transcripts from GCS and generate content using Vertex AI.

    Expected JSON payload:
    {
        "transcripts": [
            "gs://bucket/path/to/transcript1.txt",
            "gs://bucket/path/to/transcript2.txt",
            ...
        ],
        "topic": "desired topic"  // optional
    }
    """
    try:
        request_json = request.get_json(silent=True)
        if not request_json:
            logging.error("No JSON payload received")
            return jsonify({"error": "Invalid or missing JSON in request"}), 400

        transcripts_uris = request_json.get('transcripts', [])
        topic = request_json.get('topic', "")
        propmpt = request_json.get('prompt', "Generate a summary from the provided transcripts.")

        if not transcripts_uris:
            logging.error("No transcripts provided in the request")
            return jsonify({"error": "No transcripts provided"}), 400

        logging.info(f"Received transcripts URIs: {transcripts_uris}")
        logging.info(f"Topic: {topic}")

        # Create Part objects for each transcript
        parts = []
        for uri in transcripts_uris:
            try:
                part = Part.from_uri(uri, mime_type="text/plain")
                parts.append(part)
            except Exception as e:
                logging.error(f"Error creating Part from URI {uri}: {e}")
                return jsonify({"error": f"Invalid URI: {uri}"}), 400

        # Optionally, add the topic as a prompt or instruction
        if topic:
            parts.append("Topic of the transcripts is: " + topic)

        parts.append(prompt)
        
        # Initialize the Generative Model
        PROJECT_ID = "q-view-436314"
        LOCATION = "europe-west3"  # Adjust based on your requirements

        # Initialize Vertex AI
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        model_name = "gemini-1.5-flash-002"  # Replace with your desired model
        try:
            model = GenerativeModel(model_name)
            logging.info(f"Initialized GenerativeModel: {model_name}")
        except Exception as e:
            logging.error(f"Error initializing GenerativeModel {model_name}: {e}")
            return jsonify({"error": "Failed to initialize Generative Model"}), 500

        # Generate content
        try:
            response = model.generate_content(parts)
            generated_text = response.text
            logging.info("Content generation successful")
        except Exception as e:
            logging.error(f"Error generating content: {e}")
            return jsonify({"error": "Content generation failed"}), 500

        # Return the generated content
        return jsonify({"generated_content": generated_text}), 200

    except Exception as e:
        logging.exception(f"Unhandled exception: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
