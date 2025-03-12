import streamlit as st
import streamlit.components.v1 as components

def voice_input_component():
    """Custom component for voice input using Web Speech API"""
    # JavaScript code for voice recognition
    voice_js = """
    <div style="font-family: 'Consolas', 'Monaco', 'Courier New', monospace;">
        <button id="startButton" style="background-color: #4caf50; color: black; border: 1px solid #4caf50; border-radius: 0; padding: 8px 12px; cursor: pointer; font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-weight: 500; display: flex; align-items: center; justify-content: center; gap: 8px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M8 8a3 3 0 0 0 3-3V3a3 3 0 0 0-6 0v2a3 3 0 0 0 3 3z"/>
                <path d="M5 6.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5z"/>
                <path d="M8 0a4 4 0 0 0-4 4v2a4 4 0 0 0 8 0V4a4 4 0 0 0-4-4zm0 1a3 3 0 0 1 3 3v2a3 3 0 0 1-6 0V4a3 3 0 0 1 3-3z"/>
                <path d="M10.828 10.828a4 4 0 0 1-7.656 0h.06c0-.012 0-.024-.002-.036v-.276A1 1 0 0 1 4 9h8a1 1 0 0 1 .768.36v.276c0 .012 0 .024-.002.036h.06a4 4 0 0 1-7.656 0z"/>
                <path d="M8 11a5 5 0 0 0-5 5v3h10v-3a5 5 0 0 0-5-5z"/>
            </svg>
            <span>Voice Input</span>
        </button>
        <div id="status" style="margin-top:8px; color: #4caf50; font-size: 0.875rem;"></div>
        <div id="result" style="margin-top:8px; min-height: 30px; padding: 8px; border: 1px solid #333; background-color: #000000; color: #4caf50;"></div>
        
        <script>
            const startButton = document.getElementById('startButton');
            const statusDiv = document.getElementById('status');
            const resultDiv = document.getElementById('result');
            
            // Check if browser supports speech recognition
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            
            if (!SpeechRecognition) {
                statusDiv.innerHTML = "Your browser doesn't support voice recognition. Try Chrome or Edge.";
                startButton.disabled = true;
            } else {
                const recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = true;
                recognition.lang = 'en-US';
                
                let finalTranscript = '';
                
                recognition.onstart = () => {
                    statusDiv.innerHTML = "Listening... Speak now.";
                    startButton.disabled = true;
                    resultDiv.innerHTML = "";
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
                    
                    resultDiv.innerHTML = 
                        `<div style="color: #4caf50; font-weight: medium;">${finalTranscript}</div>` + 
                        `<div style="color: #666666;">${interimTranscript}</div>`;
                };
                
                recognition.onerror = (event) => {
                    statusDiv.innerHTML = `Error occurred: ${event.error}`;
                    startButton.disabled = false;
                };
                
                recognition.onend = () => {
                    statusDiv.innerHTML = "Voice recognition ended.";
                    startButton.disabled = false;
                    
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
                
                startButton.onclick = () => {
                    recognition.start();
                };
            }
        </script>
    </div>
    """
    
    # Component with default height
    component_value = components.html(voice_js, height=130)
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