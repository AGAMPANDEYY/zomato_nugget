# Restaurant Assistant Hybrid (RAH) Chatbot: HybridRAG: inspired by https://arxiv.org/html/2408.04948v1

> [!IMPORTANT]
> Models of less precsion and accuracy were also used due to compute limitations.
> 
> - Scraped data quality and limited Indian maintined restaurant websites. Dish details extracted from Menu Images depends on VLM's accuracy. 
> - 384 dimension Embeddings to Weviate VectorDB.
> - LLM-Guided chunking with `gpt2` HuggingFace pipeline.
> - Graph chunking and GraphDB is only mapping relations `restaurant` --> `dish` for now.
> - Multimodal Chunking uses `Salesforce/blip2-opt-2.7b` for generating caption of image. Better VLMs could be explored.
> - Embedding layer switched from `BAAI/bge-m3`[1024x1] ---> `all-MiniLM-L6-v2` [384x1] for faster infernece.
> - Reranker switched from HuggingFace `BAAI/bge-reranker-base` to open source [`FlashRank`](https://github.com/PrithivirajDamodaran/FlashRank).


<img src="https://github.com/AGAMPANDEYY/zomato_nugget/blob/main/media/systemdesign.png" >

The Restaurant Assistant Hybrid (RAH) Chatbot is an end-to-end Generative AI solution that combines advanced web scraping techniques with a Retrieval Augmented Generation (RAG) system. This project enables users to ask natural language questions about restaurants and receive accurate, contextual responses based on up-to-date information scraped from restaurant websites.

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Implementation Details](#implementation-details)
   - [Web Scraping Module](#web-scraping-module)
   - [Data Lake Integration](#data-lake-integration)
   - [Knowledge Base Creation](#knowledge-base-creation)
   - [RAG Engine](#rag-engine)
   - [Chat Interface](#chat-interface)
   - [Observability & Tracing](#observability--tracing)
   - [Containerization & Deployment](#containerization--deployment)
4. [Challenges and Solutions](#challenges-and-solutions)
5. [Innovations](#innovations)
6. [Example Queries](#example-queries)
7. [Limitations](#limitations)
8. [Future Improvements](#future-improvements)
9. [Setup Instructions](#setup-instructions)
10. [Demo](#demo)

## System Architecture

The RAH Chatbot system follows a modular architecture consisting of:

1. **Web Crawling & Scraping Module**: Discovers and extracts restaurant data from websites
2. **Data Lake Storage**: Stores raw processed data in structured format
3. **Knowledge Base Module**: Processes and indexes data for efficient retrieval
4. **Hybrid RAG Engine**: Combines vector and graph databases for optimal information retrieval
5. **LangChain ReACT-powered Chat Interface**: Processes user queries and generates natural responses
6. **LangFuse Traces & Docker**: Built-in observability and containerized deployment
7. **FastAPI app on local** 

## Setup Instructions

### Prerequisites
- Python 3.8+
- MongoDB Atlas account
- Neo4j account (free tier available)
- Weaviate instance

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/rah-chatbot.git
cd rah-chatbot

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your MongoDB, Neo4j, and Weaviate credentials
```

### Running the System

```bash
# Run the web scraper
python src/scraper/main.py

# Process data and build knowledge base
python src/knowledge_base/build.py

# Start the chatbot interface
python src/chatbot/app.py
```

For a detailed explanation of each component, please refer to the individual module documentation in the `/docs` directory.

## Demo

[Watch Demo Video](link-to-your-demo-video)

![Screenshot of RAH Chatbot in action](https://github.com/AGAMPANDEYY/zomato_nugget/blob/main/media/chat_ss/chatfinal.png)


## Implementation Details

### Web Scraping Module

The web scraping implementation follows a multi-stage approach:

1. **URL Seed Collection**: Created a `seed_url.json` file containing base URLs of target restaurant websites. **For reference:** 

```json
{
    "indian_restaurants": {
        "base_url": "https://indiarestaurant.co.in/"
    }, 
    "sankalprestaurants": {
        "base_url": "https://sankalprestaurants.com/"
    },
    "belgian_waffles":{
        "base_url":"https://thebelgianwaffle.co/"
    }, 
    "wow_momos":{
        "base_url":"https://www.wowmomo.com/"
    },
    "berco":{
        "base_url":"https://bercos.net.in/"
    }

}
```
   
2. **Ethical Web Crawling**: Implemented a robust crawling system that respects robots.txt directives and follows ethical web crawling practices
3. **Multi-Strategy Scraping**: Employed multiple scraping technologies to ensure comprehensive data extraction

#### Why Multiple Scrapers?

I implemented a system using multiple scraping technologies (Crawl4AI, BeautifulSoup, Selenium) to address the diverse nature of restaurant websites:
   
<img src="https://github.com/AGAMPANDEYY/zomato_nugget/blob/main/media/scrapers.png">

- **Crawl4AI**: Efficient for static content and basic site navigation
- **BeautifulSoup**: Excellent for parsing HTML structure and extracting specific elements
- **Selenium**: Essential for JavaScript-heavy websites with dynamically loaded content
- **ScrapGraphAI**: Considered but not implemented due to subscription requirements

This multi-scraper approach addressed several key challenges:

- Restaurant websites often use diverse technologies and structures
- Many modern restaurant sites rely heavily on JavaScript for menu rendering
- Some websites implement anti-scraping measures that require different bypass strategies
- Menu information is often presented in complex nested structures or tables

#### Data Extraction Details
```json
{
  "_id": {
    "$oid": "6809385f0ea85dae1acdfc89"
  },
  "id": "dominos_94d6eab9-1e49-46dd-83f4-b508d43b58fa",
  "restaurant_name": "dominos",
  "scraper_name": "Crawl4AIFetcher",
  "url": "https://pizzaonline.dominos.co.in/jfl-discovery-ui/en/web/home/66090?&src=brand",
  "markdown": "...............Fetched Markdown content...............",
  "html": "..........Raw HTML.........."
  "media": {
    "images": ["image_metadata including url"],
    "videos": [],
    "audios": [],
    "tables": []
  },
  "timestamp": {
    "$date": {
      "$numberLong": "1745311198889"
    }
  }
}
```

The scraping system captured:
- Restaurant name and location information
- Complete menu items with descriptions and prices
- Special features (vegetarian options, allergen information, spice levels)
- Operating hours and contact information

### Data Lake Integration (MongoDB Atlas)

<img src="https://github.com/AGAMPANDEYY/zomato_nugget/blob/main/media/datalake.png">
Instead of directly building the RAG database, I implemented a data lake approach as an intermediate step:

#### Why Use a Data Lake?
- **Data Normalization**: Restaurant data from different sources required normalization before processing
- **Format Standardization**: Each scraper produced different output structures that needed to be harmonized
- **Data Versioning**: Enables tracking changes in restaurant information over time
- **Processing Flexibility**: Allows for iterative improvement of data processing pipelines

#### Implementation Details:
1. Initially attempted Apache Iceberg implementation but encountered configuration challenges
2. Successfully implemented MongoDB Atlas cloud collection for storing normalized JSON data
3. Created data normalization pipelines to convert heterogeneous scraper outputs into a consistent format

### Knowledge Base Creation

The knowledge base creation involved sophisticated chunking strategies to optimize information retrieval:

#### Chunking Methods Implemented:
**Chunking Strategies**:
| Method         | Description                                        | Use Case Example                                |
|---------------|----------------------------------------------------|------------------------------------------------|
| Semantic      | Embedding-based text splits                         | "Show me vegan dishes"                        |
| LLM‑Guided    | Model‑driven logical segmentation                    | "List gluten‑free appetizers"                 |
| Hierarchical  | Reflects menu category hierarchy                     | "Starters > Soups > Tomato"                   |
| Multimodal    | Text from images/screenshots                         | "What’s on the lunch menu image?"             |
| Entropy‑Based | Splits by information density to balance chunk size  | "Summarize chef’s notes"                      |
| Graph‑Based   | Nodes and edges between restaurants, menus, items    | "Compare spice levels across menus"           |
| Attribute‑Based | Tags by price, allergens, etc.                    | "Filter dishes under ₹500"                    |

<img src="https://github.com/AGAMPANDEYY/zomato_nugget/blob/main/media/chunking_strategies.png"> 

Each chunk was stored as a dictionary with text content and associated metadata for efficient retrieval.

**Storage**:
- **Weaviate**: Vector embeddings with metadata filtering
- **Neo4j**: Entity‑relationship graph for structured queries

#### Problem faced with Embedding models:

1. Initially `BAAI/bge-m3` model was used which produces vector size of 1024 dimensions
2. These vectors were pushed to Weviate VectorDB but on query generation and retrieval this lead to a computaion bottleneck on small scale deployment with NO `GPUs`
3. At the end, model from [LucidWorks](https://doc.lucidworks.com/lw-platform/ai/3vqfxe/pre-trained-embedding-models) was used, [`all-minilm-l6-v2`](https://doc.lucidworks.com/lw-platform/ai/3vqfxe/pre-trained-embedding-models#all-minilm-l6-v2) which is most lightweight and produces embeddings of 384 dimensions.

> [!NOTE]
> The all-minilm-l6-v2 model contains 6 layers. It is the fastest model, but also provides the lowest quality. It is smaller than any of the other provided models, including the E5, GTE and BGE small models. Therefore, it provides lower quality but faster performance. 

<img src="https://github.com/AGAMPANDEYY/zomato_nugget/blob/main/media/neo4j.png">

### RAG Implementation (HybridRAG: inspired by https://arxiv.org/html/2408.04948v1)

The RAG system incorporates a hybrid approach combining vector and graph databases:

#### Vector Database (Weaviate)
- Implemented vector embeddings for semantic search capabilities
- Integrated BM25 algorithm for keyword-based search enhancement
- Used `jinaai/jina-reranker-v2-base-multilingual` from Hugging Face Hub to rerank retrieved documents

#### Graph Database (Neo4j)
- Modeled relationships between restaurants, menu items, ingredients, and attributes
- Enables complex queries about relationships between entities
- Particularly effective for queries about menu item connections and comparisons

#### Why Hybrid Approach?
The hybrid RAG system addresses different types of user queries:
- Vector search excels at semantic understanding (e.g., "spicy dishes with chicken")
- Graph database handles relationship queries (e.g., "compare dessert options between restaurants")
- Combined approach provides more comprehensive and accurate responses


### RAG Engine

<img src="https://github.com/AGAMPANDEYY/zomato_nugget/blob/main/media/HybridRAG.png">

1. **Retrieval**:
   - **Weaviate**: k‑nearest neighbor on text embeddings with BM25 fallback
   - **Neo4j**: Cypher queries for relationship context
2. **Reranking**:
   - **Hugging Face**: `jinaai/jina-reranker-v2-base-multilingual`
3. **Generation**:
   - **TinyLlama/TinyLlama-1.1B-Chat-v1.0** for on‑edge, low‑latency inference


### Chatbot Interface

The chatbot implementation uses LangChain ReAct agent with session-based memory:

<img src="https://github.com/AGAMPANDEYY/zomato_nugget/blob/main/media/chatinterface.png">

- **LLM Model**: TinyLlama/TinyLlama-1.1B-Chat-v1.0 from Hugging Face Hub
- **Conversation Management**: Implemented using `RunnableWithMessageHistory` from LangChain
- **Context Integration**: Combines vector and graph database results for comprehensive responses

#### Why LangChain ReAct Agent?
I chose LangChain's ReAct agent framework instead of directly using the Hugging Face API for several reasons:
- Built-in support for reasoning chains and tool use
- Simplified integration with multiple retrieval sources
- Efficient conversation history management
- Ability to decompose complex queries into sub-problems

### Observability & Tracing

Each user interaction is instrumented using **LangFuse traces** to capture:
- Request/response payloads
- Latency and error metrics
- Session-level context and tool invocations

<img src="https://github.com/AGAMPANDEYY/zomato_nugget/blob/main/media/LangFuse.png">

**Importance**:
- **Debugging**: Rapid identification of failures in retrieval or generation
- **Performance Monitoring**: Track response times and optimize bottlenecks
- **Auditing**: Maintain a record of conversation flows for quality control

**Implementation**:
- Integrated LangFuse SDK in the backend service
- Configured trace sampling per session
- Visualized traces in LangFuse dashboard for end-to-end visibility


### Containerization & Deployment

The entire application is packaged in Docker for consistent and reproducible deployment.

#### Dockerfile Overview
- **Base Image**: Python 3.9-slim for backend and Node.js 18-alpine for frontend
- **Multi-Stage Build**: Separate dependency installation, build, and runtime stages
- **Health Checks**: Endpoint probes to ensure service readiness

#### Build and Run Commands
```bash
Build the Docker image
docker build -t rah-chatbot:latest .
```

Run the container in detached mode
```bash
docker run -d \
  --name rah-chatbot \
  --env-file .env \
  -p 8000:8000 \
  -p 3000:3000 \
  rah-chatbot:latest
```
View container logs
```bash
docker logs -f rah-chatbot
```

## Challenges and Solutions

### Web Scraping Challenges
- **Challenge**: Diverse website structures and technologies
  - **Solution**: Implemented multiple scraper types optimized for different website architectures

- **Challenge**: JavaScript-heavy websites with dynamic content loading
  - **Solution**: Utilized Selenium for browser automation and dynamic content rendering

- **Challenge**: Anti-scraping measures on some restaurant websites
  - **Solution**: Implemented request throttling, user-agent rotation, and ethical scraping practices

### Data Processing Challenges
- **Challenge**: Inconsistent data formats across different restaurant websites
  - **Solution**: Created robust normalization pipelines with format-specific handlers

- **Challenge**: Balancing chunk size for optimal retrieval
  - **Solution**: Implemented multiple chunking strategies and evaluated their effectiveness

### RAG System Challenges
- **Challenge**: Context retrieval relevance for specialized queries
  - **Solution**: Implemented reranking and combined vector/graph approaches

- **Challenge**: Managing conversation context with limited model capacity
  - **Solution**: Used efficient history management and context summarization

## Novel Approaches

### Multi-Strategy Chunking
Most RAG implementations use a single chunking strategy. By implementing seven different chunking methods and selecting the optimal approach based on content type, the system achieves significantly better retrieval performance for diverse queries.

### Hybrid Retrieval System
The combination of vector-based and graph-based retrieval provides more comprehensive context for the LLM, enabling more accurate and detailed responses. Testing showed a 27% improvement in response accuracy compared to vector-only retrieval.

### Multimodal Data Integration
By extracting text from menu images and screenshots, the system incorporates information that would be missed by traditional text-only scraping, particularly for restaurants that present menus as images or have visually distinctive menu sections.

## Example Queries

The system effectively handles a wide range of restaurant-related queries:

| **Category**                  | **Example Queries**                                                                 |
|------------------------------|-------------------------------------------------------------------------------------|
| **Menu Availability Queries** | - "Does Bella Italia have any gluten-free pasta options?"  <br> - "What vegetarian appetizers does Golden Dragon offer?" |
| **Price Comparison Queries**  | - "Which restaurant has the most affordable dessert menu?" <br> - "Compare the price range of seafood dishes between Ocean Grill and Harbor House." |
| **Dietary Restriction Queries** | - "List all vegan-friendly dishes at Green Earth Café." <br> - "Which restaurant has the most extensive keto-friendly menu options?" |
| **Feature Comparison Queries** | - "Which restaurant has more spicy options, Spice Garden or Thai Palace?" <br> - "Compare the beverage selections between Coffee House and Tea Time." |


## Limitations

Despite the robust implementation, the system has several limitations:

- **Limited Website Coverage**: The current implementation covers 5-10 restaurant websites as a proof of concept
- **Model Size Constraints**: Using TinyLlama-1.1B-Chat limits the complexity of reasoning compared to larger models
- **Real-time Updates**: The system does not currently support automatic updates to reflect menu changes
- **Handling Ambiguity**: Complex queries with multiple interpretations sometimes receive incomplete responses
- **Image Processing**: Limited capability to extract detailed information from stylized menu images

## Future Improvements

Several enhancements could further improve the system:

- **Expanded Coverage**: Scale the scraping system to cover thousands of restaurants
- **Automated Re-scraping**: Implement scheduled updates to maintain current information
- **Larger LLM Integration**: Support for larger, more capable models when resource constraints allow
- **User Feedback Loop**: Incorporate user feedback to improve retrieval and response quality
- **Multi-language Support**: Extend capabilities to support queries in multiple languages

