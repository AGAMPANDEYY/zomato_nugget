document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatContainer = document.getElementById('chat-container');
    const welcomeScreen = document.getElementById('welcome-screen');
    const exampleQueries = document.querySelectorAll('.example-query');
    const featureCards = document.querySelectorAll('.feature-card');
    
    // Chat history
    let chatHistory = [];
    
    // Auto-resize textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.scrollHeight > 150) {
            this.style.height = '150px';
        }
    });
    
    // Example query click handler
    exampleQueries.forEach(query => {
        query.addEventListener('click', function() {
            messageInput.value = this.textContent.trim();
            messageInput.focus();
            // Auto adjust height
            messageInput.dispatchEvent(new Event('input'));
        });
    });
    
    // Feature card click handler
    featureCards.forEach(card => {
        card.addEventListener('click', function() {
            const category = this.querySelector('p').textContent;
            let message = "";
            
            switch(category) {
                case "Veg Options":
                    message = "Show me restaurants with the best vegetarian options";
                    break;
                case "Gourmet":
                    message = "What are the top gourmet restaurants available?";
                    break;
                case "Healthy":
                    message = "Recommend some healthy food options near me";
                    break;
                case "Quick Delivery":
                    message = "Which restaurants offer the fastest delivery?";
                    break;
                case "Gift Cards":
                    message = "Tell me about restaurant gift card options";
                    break;
                case "Offers":
                    message = "What special offers are available right now?";
                    break;
                default:
                    message = "Tell me more about " + category;
            }
            
            messageInput.value = message;
            messageInput.focus();
            // Auto adjust height
            messageInput.dispatchEvent(new Event('input'));
        });
    });
    
    // Send message on Enter key (without shift)
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Send button click handler
    sendButton.addEventListener('click', sendMessage);
    
    // Send message function
    function sendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            // Hide welcome screen on first message
            if (welcomeScreen.style.display !== 'none') {
                welcomeScreen.style.display = 'none';
            }
            
            // Add user message
            addMessage(message, 'user');
            
            // Format history for the API request
            const formattedHistory = chatHistory.map(entry => ({
                role: entry.role === 'user' ? 'user' : 'assistant',
                content: entry.content
            }));
            
            // Add current message to history
            chatHistory.push({role: 'user', content: message});
            
            // Clear input
            messageInput.value = '';
            messageInput.style.height = 'auto';
            
            // Show typing indicator
            showTypingIndicator();
            
            // Process the message and generate response using the FastAPI endpoint
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    message: message,
                    history: formattedHistory
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                removeTypingIndicator();
                const botResponse = data.response || "Sorry, I didn't understand that.";
                addMessage(botResponse, 'bot');
                
                // Update chat history from response
                chatHistory = data.history || chatHistory;
                
                // If history wasn't returned, add the response to our local history
                if (!data.history) {
                    chatHistory.push({ role: 'assistant', content: botResponse });
                }
            })
            .catch(error => {
                removeTypingIndicator();
                console.error('Error communicating with FastAPI:', error);
                addMessage("Oops! Something went wrong. Please try again later.", 'bot');
            });
        }
    }
    
    // Add message to chat
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        if (sender === 'bot') {
            const botAvatar = document.createElement('div');
            botAvatar.className = 'bot-avatar';
            const botIcon = document.createElement('i');
            botIcon.className = 'fas fa-robot';
            botAvatar.appendChild(botIcon);
            messageDiv.appendChild(botAvatar);
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = formatMessageText(text);
        messageDiv.appendChild(contentDiv);
        
        chatContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // Format message text (handle newlines, links, etc.)
    function formatMessageText(text) {
        // Convert URLs to links
        text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
        
        // Convert newlines to <br>
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }
    
    // Show typing indicator
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message typing-indicator';
        
        const botAvatar = document.createElement('div');
        botAvatar.className = 'bot-avatar';
        const botIcon = document.createElement('i');
        botIcon.className = 'fas fa-robot';
        botAvatar.appendChild(botIcon);
        typingDiv.appendChild(botAvatar);
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
        typingDiv.appendChild(contentDiv);
        
        chatContainer.appendChild(typingDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // Remove typing indicator
    function removeTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Clear chat function
    window.clearChat = function() {
        // Remove all messages except the typing indicator
        while (chatContainer.firstChild) {
            if (!chatContainer.firstChild.classList.contains('typing-indicator')) {
                chatContainer.removeChild(chatContainer.firstChild);
            } else {
                break;
            }
        }
        
        // Reset chat history
        chatHistory = [];
        
        // Add back the welcome screen
        welcomeScreen.style.display = 'block';
        chatContainer.appendChild(welcomeScreen);
    };
    
    // Add CSS for typing indicator
    const style = document.createElement('style');
    style.textContent = `
        .typing-dots {
            display: flex;
            align-items: center;
            height: 20px;
        }
        
        .typing-dots span {
            height: 8px;
            width: 8px;
            margin-right: 4px;
            border-radius: 50%;
            background-color: #86898E;
            display: inline-block;
            animation: pulse 1.5s infinite ease-in-out;
        }
        
        .typing-dots span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-dots span:nth-child(3) {
            animation-delay: 0.4s;
            margin-right: 0;
        }
        
        @keyframes pulse {
            0%, 60%, 100% {
                transform: scale(1);
                opacity: 0.6;
            }
            30% {
                transform: scale(1.5);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
});