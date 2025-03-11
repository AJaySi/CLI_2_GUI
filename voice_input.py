import streamlit as st
import streamlit.components.v1 as components

def voice_input_component():
    """Custom component for voice input using Web Speech API"""
    components.html(
        """
        <div id="voice_container" style="display: flex; align-items: center;">
            <button id="voice_button" 
                    style="background-color: #3498db; 
                           color: white; 
                           border: none; 
                           border-radius: 4px; 
                           padding: 8px; 
                           cursor: pointer;
                           transition: all 0.3s ease;">
                🎤
            </button>
            <div id="status" style="margin-left: 10px; color: #bbb;"></div>
        </div>

        <script>
        const voiceButton = document.getElementById('voice_button');
        const status = document.getElementById('status');
        let recognition = null;

        // Initialize speech recognition
        function initSpeechRecognition() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (SpeechRecognition) {
                recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-US';

                recognition.onstart = () => {
                    voiceButton.style.backgroundColor = '#e74c3c';
                    status.textContent = 'Listening...';
                    status.style.opacity = '1';
                };

                recognition.onresult = (event) => {
                    const text = event.results[0][0].transcript;
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: text
                    }, '*');
                    status.textContent = 'Command received: ' + text;
                };

                recognition.onerror = (event) => {
                    console.error('Speech recognition error:', event.error);
                    status.textContent = 'Error: ' + event.error;
                    status.style.opacity = '1';
                    resetButton();
                };

                recognition.onend = () => {
                    resetButton();
                    setTimeout(() => {
                        status.style.opacity = '0';
                    }, 2000);
                };
            } else {
                status.textContent = 'Speech recognition not supported';
                status.style.opacity = '1';
                voiceButton.disabled = true;
            }
        }

        function resetButton() {
            voiceButton.style.backgroundColor = '#3498db';
        }

        voiceButton.onclick = () => {
            if (!recognition) {
                initSpeechRecognition();
            }

            if (recognition) {
                if (voiceButton.style.backgroundColor === 'rgb(231, 76, 60)') {
                    recognition.stop();
                } else {
                    recognition.start();
                }
            }
        };
        </script>
        """,
        height=50,
    )

def handle_voice_input():
    """Handle voice input from the JavaScript component"""
    result = components.html(
        """
        <script>
        // Listen for voice input messages
        window.addEventListener('message', function(e) {
            if (e.data.type === 'streamlit:setComponentValue') {
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: e.data.value
                }, '*');
            }
        });
        </script>
        """,
        height=0
    )

    return result if result is not None else ""