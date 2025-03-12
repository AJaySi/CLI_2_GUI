import streamlit as st
import streamlit.components.v1 as components

def voice_input_component():
    """Custom component for voice input using Web Speech API (icon-only version)"""
    # JavaScript code for voice recognition
    voice_js = """
    <div style="font-family: 'Consolas', 'Monaco', 'Courier New', monospace;">
        <button 
            id="startButton" 
            aria-label="Start voice input" 
            title="Click to start voice input"
            style="background-color: #61afef; color: #282c34; border: 1px solid #61afef; border-radius: 4px; padding: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; width: 38px; height: 36px; margin: 0;"
        >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" aria-hidden="true" viewBox="0 0 16 16">
                <path d="M8 8a3 3 0 0 0 3-3V3a3 3 0 0 0-6 0v2a3 3 0 0 0 3 3z"/>
                <path d="M5 6.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5z"/>
                <path d="M8 0a4 4 0 0 0-4 4v2a4 4 0 0 0 8 0V4a4 4 0 0 0-4-4zm0 1a3 3 0 0 1 3 3v2a3 3 0 0 1-6 0V4a3 3 0 0 1 3-3z"/>
                <path d="M10.828 10.828a4 4 0 0 1-7.656 0h.06c0-.012 0-.024-.002-.036v-.276A1 1 0 0 1 4 9h8a1 1 0 0 1 .768.36v.276c0 .012 0 .024-.002.036h.06a4 4 0 0 1-7.656 0z"/>
                <path d="M8 11a5 5 0 0 0-5 5v3h10v-3a5 5 0 0 0-5-5z"/>
            </svg>
            <span class="sr-only" style="position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border-width: 0;">
                Start voice input
            </span>
        </button>
        <div 
            id="status" 
            aria-live="polite" 
            role="status"
            style="margin-top:6px; color: #98c379; font-size: 0.8rem; height: 24px; font-weight: 500;">
        </div>
        
        <script>
            const startButton = document.getElementById('startButton');
            const statusDiv = document.getElementById('status');
            
            // Check if browser supports speech recognition
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            
            if (!SpeechRecognition) {
                statusDiv.innerHTML = "Not supported";
                startButton.disabled = true;
                startButton.style.opacity = "0.5";
            } else {
                const recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = true;
                recognition.lang = 'en-US';
                
                let finalTranscript = '';
                
                recognition.onstart = () => {
                    statusDiv.innerHTML = "Listening...";
                    statusDiv.setAttribute('aria-label', 'Listening for your voice input');
                    startButton.disabled = true;
                    startButton.setAttribute('aria-pressed', 'true');
                    startButton.setAttribute('aria-label', 'Voice recognition active, listening for input');
                    startButton.style.backgroundColor = "#e06c75"; // Red while recording
                    finalTranscript = '';
                };
                
                recognition.onresult = (event) => {
                    let interimTranscript = '';
                    
                    for (let i = event.resultIndex; i < event.results.length; i++) {
                        const transcript = event.results[i][0].transcript;
                        if (event.results[i].isFinal) {
                            finalTranscript += transcript;
                        } else {
                            interimTranscript += transcript;
                        }
                    }
                    
                    // Only update status with interim
                    if (interimTranscript) {
                        statusDiv.innerHTML = interimTranscript;
                        statusDiv.setAttribute('aria-label', 'Heard: ' + interimTranscript);
                    }
                };
                
                recognition.onerror = (event) => {
                    const errorMessage = `Error: ${event.error}`;
                    statusDiv.innerHTML = errorMessage;
                    statusDiv.setAttribute('aria-label', 'Voice recognition error: ' + event.error);
                    startButton.disabled = false;
                    startButton.setAttribute('aria-pressed', 'false');
                    startButton.setAttribute('aria-label', 'Start voice input');
                    startButton.style.backgroundColor = "#61afef"; // Back to blue
                };
                
                recognition.onend = () => {
                    statusDiv.innerHTML = finalTranscript ? "Voice input received" : "Ready";
                    statusDiv.setAttribute('aria-label', finalTranscript ? 'Voice input received: ' + finalTranscript : 'Voice recognition ready');
                    startButton.disabled = false;
                    startButton.setAttribute('aria-pressed', 'false');
                    startButton.setAttribute('aria-label', 'Start voice input');
                    startButton.style.backgroundColor = "#61afef"; // Back to blue
                    
                    // Send the recognized text to Streamlit
                    if (finalTranscript) {
                        const data = {
                            text: finalTranscript
                        };
                        
                        // Use Streamlit's sendBackData to communicate with the Python code
                        window.parent.postMessage({
                            type: "streamlit:setComponentValue",
                            value: data
                        }, "*");
                    }
                };
                
                // Support both click and keyboard events
                startButton.onclick = () => {
                    recognition.start();
                };
                
                // Make sure keyboard users can access the button
                startButton.onkeydown = (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        recognition.start();
                    }
                };
            }
        </script>
    </div>
    """
    
    # Component with minimal height, exactly matching input field height
    component_value = components.html(voice_js, height=45)
    return component_value

def handle_voice_input():
    """Handle voice input from the JavaScript component"""
    voice_data = voice_input_component()
    
    if voice_data and isinstance(voice_data, dict) and 'text' in voice_data:
        recognized_text = voice_data['text']
        # Return the recognized text
        return recognized_text
    
    # Return None if no valid voice input
    return None