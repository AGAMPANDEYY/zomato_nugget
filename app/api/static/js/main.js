document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatContainer = document.getElementById('chat-container');
    const welcomeScreen = document.getElementById('welcome-screen');
    const exampleQueries = document.querySelectorAll('.example-query');
    const featureCards = document.querySelectorAll('.feature-card');
    
    // Sample restaurant data (in a real application this would come from an API)
    const restaurantData = {
        "La Petite Maison": {
            cuisine: "French",
            priceRange: "$$$",
            specialties: ["Truffle Risotto", "Duck Confit", "Crème Brûlée"],
            dietaryOptions: ["vegetarian options available", "gluten-free options"]
        },
        "Tandoor Palace": {
            cuisine: "Indian",
            priceRange: "$$",
            specialties: ["Butter Chicken", "Garlic Naan", "Lamb Biryani"],
            dietaryOptions: ["vegetarian", "vegan options", "halal"]
        },
        "Spice Garden": {
            cuisine: "Thai",
            priceRange: "$$",
            specialties: ["Pad Thai", "Green Curry", "Mango Sticky Rice"],
            dietaryOptions: ["vegetarian", "gluten-free options"]
        },
        "Happy Burger": {
            cuisine: "American",
            priceRange: "$",
            specialties: ["Classic Cheeseburger", "Loaded Fries", "Milkshakes"],
            dietaryOptions: ["vegetarian options", "gluten-free buns available"]
        },
        "Mirage": {
            cuisine: "Mediterranean",
            priceRange: "$$$",
            specialties: ["Seafood Paella", "Lamb Tagine", "Baklava"],
            dietaryOptions: ["vegetarian options", "pescatarian"]
        },
        "The Grand Pavilion": {
            cuisine: "Pan-Asian",
            priceRange: "$$$",
            specialties: ["Peking Duck", "Sushi Platter", "Matcha Cheesecake"],
            dietaryOptions: ["vegetarian options", "gluten-free available"]
        }
    };
    
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
            chatHistory.push({role: 'user', content: message});
            
            // Clear input
            messageInput.value = '';
            messageInput.style.height = 'auto';
            
            // Show typing indicator
            showTypingIndicator();
            
            // Process the message and generate response
            setTimeout(() => {
                removeTypingIndicator();
                const botResponse = generateResponse(message);
                addMessage(botResponse, 'bot');
                chatHistory.push({role: 'bot', content: botResponse});
            }, 1000 + Math.random() * 1000); // Random delay between 1-2 seconds
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
        
        // Bold restaurant names
        Object.keys(restaurantData).forEach(restaurant => {
            const regex = new RegExp(restaurant, 'g');
            text = text.replace(regex, `<strong>${restaurant}</strong>`);
        });
        
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
    
    // Generate response based on user query
    function generateResponse(query) {
        query = query.toLowerCase();
        
        // Check for greetings
        if (/^(hi|hello|hey|greetings).*/i.test(query)) {
            return "Hello! Welcome to Zomato Restaurant Concierge. How can I assist you with your dining needs today?";
        }
        
        // Check for restaurant mentions
        for (const restaurant in restaurantData) {
            if (query.includes(restaurant.toLowerCase())) {
                const data = restaurantData[restaurant];
                
                // Check for various query types
                if (query.includes("menu") || query.includes("dish") || query.includes("specialties")) {
                    return `${restaurant} specializes in ${data.cuisine} cuisine. Their signature dishes include ${data.specialties.join(", ")}. The price range is ${data.priceRange}.`;
                }
                
                if (query.includes("vegetarian") || query.includes("vegan") || query.includes("gluten")) {
                    return `${restaurant} offers the following dietary options: ${data.dietaryOptions.join(", ")}.`;
                }
                
                if (query.includes("price") || query.includes("cost") || query.includes("expensive")) {
                    return `${restaurant} falls in the ${data.priceRange} price range. They offer ${data.cuisine} cuisine with dishes like ${data.specialties.slice(0, 2).join(" and ")}.`;
                }
                
                // Default response for restaurant
                return `${restaurant} is a ${data.cuisine} restaurant with a price range of ${data.priceRange}. Their specialties include ${data.specialties.join(", ")}. They accommodate ${data.dietaryOptions.join(", ")}.`;
            }
        }
        
        // Check for cuisine or category queries
        if (query.includes("vegetarian") || query.includes("vegan")) {
            return "Several restaurants offer excellent vegetarian options. Spice Garden and Tandoor Palace have extensive vegetarian menus. Would you like specific dish recommendations from either of these restaurants?";
        }
        
        if (query.includes("fine dining") || query.includes("gourmet")) {
            return "For an upscale dining experience, I recommend La Petite Maison, Mirage, or The Grand Pavilion. Each offers exceptional service and sophisticated culinary creations. Would you like to know more about any of these restaurants?";
        }
        
        if (query.includes("compare")) {
            if (query.includes("tandoor palace") && query.includes("spice garden")) {
                return "Comparing Tandoor Palace and Spice Garden:\n\nTandoor Palace offers Indian cuisine with a price range of $$. They're known for rich, flavorful dishes with varying spice levels from mild to very hot.\n\nSpice Garden serves Thai cuisine, also in the $$ range, with dishes that balance sweet, sour, and spicy flavors. Their spice level can be adjusted according to preference.";
            }
            
            if (query.includes("mirage") && query.includes("grand pavilion")) {
                return "Comparing Mirage and The Grand Pavilion:\n\nMirage offers Mediterranean cuisine in a $$$ price range with a focus on fresh seafood and traditional dishes with a modern twist.\n\nThe Grand Pavilion serves Pan-Asian cuisine, also in the $$$ range, featuring a diverse selection of dishes from various Asian countries with elegant presentation.";
            }
            
            return "I'd be happy to compare restaurants for you. Could you specify which restaurants you'd like to compare?";
        }
        
        // Default response
        return "Thank you for your question. I can provide information about restaurant menus, prices, dietary options, and more. Could you please specify which restaurant or cuisine you're interested in?";
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
        chatContainer.appendChild(welcomeScreen);
        welcomeScreen.style.display = 'block';
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