"""
Flask web app to view Kitsu Output File metadata.
This provides a UI for the output files that Kitsu's interface doesn't show.

Usage:
    python output_file_viewer.py
    
Access:
    http://localhost:5000/output-file/<output_file_id>
"""
from flask import Flask, render_template, jsonify, Response
import gazu
import os
import tempfile

app = Flask(__name__)

# Kitsu configuration
KITSU_HOST = os.getenv('KITSU_HOST', 'KITSU URL')
KITSU_EMAIL = os.getenv('KITSU_EMAIL', 'KITSU USER')
KITSU_PASSWORD = os.getenv('KITSU_PASSWORD', 'KITSU PASSWORD')

# Authenticate once when the app starts
gazu.set_host(KITSU_HOST)
gazu.log_in(KITSU_EMAIL, KITSU_PASSWORD)


@app.route('/')
def index():
    """Landing page."""
    return """
    <html>
        <head>
            <title>Kitsu Output File Viewer</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }
                h1 { color: #333; }
                p { color: #666; line-height: 1.6; }
                code { 
                    background: #e0e0e0; 
                    padding: 2px 6px; 
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }
            </style>
        </head>
        <body>
            <h1>🎬 Kitsu Output File Viewer</h1>
            <p>This app displays metadata for Kitsu output files that aren't visible in the main Kitsu UI.</p>
            <p>Access output files via: <code>/output-file/&lt;output_file_id&gt;</code></p>
        </body>
    </html>
    """


@app.route('/output-file/<output_file_id>')
def view_output_file(output_file_id):
    """View a specific output file's metadata."""
    try:
        # Get the output file from Kitsu
        output_file = gazu.files.get_output_file(output_file_id)
        
        if not output_file:
            return render_template('error.html', 
                                 error="Output file not found",
                                 output_file_id=output_file_id), 404
        
        # Get related entity (shot or asset)
        entity_id = output_file.get('entity_id')
        entity = None
        entity_type = None
        shot_url = None
        
        if entity_id:
            try:
                # Try as shot first
                entity = gazu.shot.get_shot(entity_id)
                entity_type = 'Shot'
                
                # Build the correct Kitsu shot URL
                kitsu_base_url = KITSU_HOST.replace('/api', '')
                project_id = entity.get('project_id')
                shot_id = entity.get('id')
                episode_id = entity.get('episode_id')
                
                if episode_id:
                    shot_url = f"{kitsu_base_url}/productions/{project_id}/episodes/{episode_id}/shots/{shot_id}/"
                else:
                    shot_url = f"{kitsu_base_url}/productions/{project_id}/shots/{shot_id}/"
                
            except:
                try:
                    # Try as asset
                    entity = gazu.asset.get_asset(entity_id)
                    entity_type = 'Asset'
                    
                    # Build asset URL
                    kitsu_base_url = KITSU_HOST.replace('/api', '')
                    project_id = entity.get('project_id')
                    asset_id = entity.get('id')
                    shot_url = f"{kitsu_base_url}/productions/{project_id}/assets/{asset_id}/"
                except:
                    pass
        
        # Get output type
        output_type = None
        output_type_id = output_file.get('output_type_id')
        if output_type_id:
            try:
                output_type = gazu.files.get_output_type(output_type_id)
            except:
                pass
        
        # Get task type
        task_type = None
        task_type_id = output_file.get('task_type_id')
        if task_type_id:
            try:
                task_type = gazu.task.get_task_type(task_type_id)
            except:
                pass
        
        # Get preview file
        preview_file_id = None
        has_preview = False
        
        try:
            task_type_id = output_file.get('task_type_id')
            
            if task_type_id and entity_id:
                # Get all tasks for this entity
                if entity_type == 'Shot':
                    tasks = gazu.task.all_tasks_for_shot(entity)
                elif entity_type == 'Asset':
                    tasks = gazu.task.all_tasks_for_asset(entity)
                else:
                    tasks = []
                
                # Find the task matching our task type
                for task in tasks:
                    if task.get('task_type_id') == task_type_id:
                        # Get previews for this task
                        previews = gazu.files.get_all_preview_files_for_task(task)
                        
                        if previews:
                            # Get the most recent preview
                            latest_preview = previews[-1]
                            preview_file_id = latest_preview.get('id')
                            has_preview = True
                            break
        except:
            pass
        
        return render_template('output_file.html',
                             output_file=output_file,
                             entity=entity,
                             entity_type=entity_type,
                             output_type=output_type,
                             task_type=task_type,
                             shot_url=shot_url,
                             preview_file_id=preview_file_id,
                             has_preview=has_preview)
    
    except Exception as e:
        return render_template('error.html',
                             error=str(e),
                             output_file_id=output_file_id), 500


@app.route('/preview/<preview_file_id>')
def get_preview(preview_file_id):
    """Proxy endpoint to fetch preview video from Kitsu."""
    try:
        # Get the preview file metadata
        preview_file = gazu.files.get_preview_file(preview_file_id)
        
        # Download the preview file to a temporary location
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"preview_{preview_file_id}.mp4")
        
        # Use Gazu's built-in download function
        gazu.files.download_preview_file(preview_file, temp_path)
        
        # Read the file and serve it
        with open(temp_path, 'rb') as f:
            video_data = f.read()
        
        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass
        
        # Return the video
        return Response(
            video_data,
            mimetype='video/mp4',
            headers={
                'Content-Type': 'video/mp4',
                'Content-Length': str(len(video_data)),
                'Accept-Ranges': 'bytes',
                'Cache-Control': 'public, max-age=31536000'
            }
        )
            
    except Exception as e:
        app.logger.error(f"Error fetching preview {preview_file_id}: {e}")
        return "Preview not available", 404


@app.route('/api/output-file/<output_file_id>')
def api_output_file(output_file_id):
    """API endpoint to get output file data as JSON."""
    try:
        output_file = gazu.files.get_output_file(output_file_id)
        return jsonify(output_file)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("🎬 Starting Kitsu Output File Viewer...")
    print(f"📡 Connected to: {KITSU_HOST}")
    print(f"👤 User: {KITSU_EMAIL}")
    print("\n🌐 Server running at: http://localhost:5000")
    print("📄 View output files at: http://localhost:5000/output-file/<id>\n")
    
    # Disable Flask's request logging for cleaner output
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    app.run(debug=False, host='0.0.0.0', port=5000)