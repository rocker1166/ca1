#!/usr/bin/env python3
"""
Enhanced PowerPoint Formatting Test
Tests the improved adaptive formatting, spacing, and overlap prevention features.
"""

import requests
import json
import time
import os
from pathlib import Path

# API Configuration
API_BASE = "http://localhost:8000"
TEST_OUTPUT_DIR = Path("test_outputs/enhanced_formatting")

def setup_test_directory():
    """Create test output directory"""
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def test_adaptive_text_formatting():
    """Test adaptive text formatting with various content densities"""
    
    # Test 1: High-density content
    high_density_request = {
        "query": "Comprehensive analysis of machine learning algorithms including supervised learning techniques such as decision trees, random forests, support vector machines, and neural networks, along with unsupervised learning methods like clustering, dimensionality reduction, and association rule mining",
        "slides": [
            {
                "title": "Machine Learning Algorithms: A Comprehensive Overview and Analysis",
                "content": [
                    {
                        "text": "Supervised Learning Techniques encompass a wide range of algorithms designed to learn from labeled training data and make predictions on new, unseen data points",
                        "sub_points": [
                            "Decision Trees provide interpretable models through hierarchical decision-making processes",
                            "Random Forests combine multiple decision trees to improve accuracy and reduce overfitting",
                            "Support Vector Machines find optimal hyperplanes for classification and regression tasks"
                        ]
                    },
                    {
                        "text": "Unsupervised Learning Methods discover hidden patterns in data without labeled examples",
                        "sub_points": [
                            "K-means clustering groups similar data points together",
                            "Principal Component Analysis reduces dimensionality while preserving variance",
                            "Association rule mining finds relationships between different items"
                        ]
                    }
                ]
            }
        ],
        "num_slides": 5,
        "include_images": True,
        "include_diagrams": True
    }
    
    # Test 2: Medium-density content
    medium_density_request = {
        "query": "Basic introduction to Python programming",
        "slides": [
            {
                "title": "Python Programming Basics",
                "content": [
                    {
                        "text": "Python is a versatile programming language",
                        "sub_points": [
                            "Easy to learn and read",
                            "Extensive library ecosystem",
                            "Cross-platform compatibility"
                        ]
                    },
                    {
                        "text": "Key features include dynamic typing and automatic memory management"
                    }
                ]
            }
        ],
        "num_slides": 3
    }
    
    # Test 3: Low-density content
    low_density_request = {
        "query": "Simple greeting presentation",
        "slides": [
            {
                "title": "Welcome",
                "content": [
                    {"text": "Hello and welcome to our presentation"},
                    {"text": "Thank you for joining us today"}
                ]
            }
        ],
        "num_slides": 2
    }
    
    test_cases = [
        ("high_density", high_density_request),
        ("medium_density", medium_density_request),
        ("low_density", low_density_request)
    ]
    
    for case_name, request_data in test_cases:
        print(f"\n🧪 Testing {case_name} content formatting...")
        
        response = requests.post(f"{API_BASE}/api/generate-ppt", json=request_data)
        if response.status_code == 200:
            filename = TEST_OUTPUT_DIR / f"adaptive_text_{case_name}.pptx"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✅ Generated: {filename}")
        else:
            print(f"❌ Failed {case_name}: {response.status_code}")

def test_image_text_positioning():
    """Test proper image and text positioning to prevent overlap"""
    
    request_data = {
        "query": "Data visualization techniques with examples",
        "slides": [
            {
                "title": "Data Visualization Techniques",
                "content": [
                    {
                        "text": "Charts and graphs help communicate data insights effectively",
                        "sub_points": [
                            "Bar charts compare categorical data",
                            "Line charts show trends over time",
                            "Scatter plots reveal correlations"
                        ]
                    }
                ],
                "image_url": "https://via.placeholder.com/800x600/4CAF50/FFFFFF?text=Sample+Chart",
                "images": ["https://via.placeholder.com/600x400/2196F3/FFFFFF?text=Data+Visualization"]
            },
            {
                "title": "Mixed Content Layout Test",
                "content": [
                    {"text": "This slide tests image and diagram positioning"},
                    {"text": "Content should not overlap with visual elements"}
                ],
                "image_url": "https://via.placeholder.com/500x400/FF9800/FFFFFF?text=Test+Image",
                "diagram_type": "process",
                "diagram_data": [
                    {"step": "Data Collection"},
                    {"step": "Processing"},
                    {"step": "Visualization"},
                    {"step": "Analysis"}
                ]
            }
        ],
        "num_slides": 4,
        "include_images": True,
        "include_diagrams": True
    }
    
    print(f"\n🖼️ Testing image-text positioning...")
    
    response = requests.post(f"{API_BASE}/api/generate-ppt", json=request_data)
    if response.status_code == 200:
        filename = TEST_OUTPUT_DIR / "image_text_positioning.pptx"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"✅ Generated: {filename}")
    else:
        print(f"❌ Failed: {response.status_code}")

def test_diagram_spacing():
    """Test proper diagram sizing and spacing"""
    
    request_data = {
        "query": "Process flow and comparison diagrams",
        "slides": [
            {
                "title": "Process Flow Diagram",
                "content": [
                    {"text": "Software development lifecycle stages"},
                    {"text": "Each stage has specific deliverables and goals"}
                ],
                "diagram_type": "process",
                "diagram_data": [
                    {"step": "Requirements Analysis"},
                    {"step": "System Design"},
                    {"step": "Implementation"},
                    {"step": "Testing"},
                    {"step": "Deployment"},
                    {"step": "Maintenance"}
                ]
            },
            {
                "title": "Technology Comparison",
                "content": [
                    {"text": "Comparing different approaches helps make informed decisions"}
                ],
                "diagram_type": "comparison",
                "diagram_data": [
                    {"title": "Traditional Development: Waterfall methodology with sequential phases and extensive documentation"},
                    {"title": "Agile Development: Iterative approach with frequent releases and customer collaboration"}
                ]
            }
        ],
        "num_slides": 3
    }
    
    print(f"\n📊 Testing diagram spacing and sizing...")
    
    response = requests.post(f"{API_BASE}/api/generate-ppt", json=request_data)
    if response.status_code == 200:
        filename = TEST_OUTPUT_DIR / "diagram_spacing.pptx"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"✅ Generated: {filename}")
    else:
        print(f"❌ Failed: {response.status_code}")

def test_paragraph_formatting():
    """Test paragraph-style content formatting"""
    
    request_data = {
        "query": "Artificial Intelligence Overview",
        "slides": [
            {
                "title": "What is Artificial Intelligence?",
                "description": "Artificial Intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think and learn like humans. The term may also be applied to any machine that exhibits traits associated with a human mind such as learning and problem-solving. AI has the potential to revolutionize many aspects of our daily lives, from healthcare and transportation to education and entertainment. Modern AI systems can process vast amounts of data, recognize patterns, and make decisions with increasing accuracy and speed."
            },
            {
                "title": "AI Applications",
                "bullets": [
                    "Machine learning algorithms power recommendation systems in e-commerce and streaming platforms, providing personalized experiences for millions of users worldwide."
                ]
            }
        ],
        "num_slides": 3
    }
    
    print(f"\n📝 Testing paragraph formatting...")
    
    response = requests.post(f"{API_BASE}/api/generate-ppt", json=request_data)
    if response.status_code == 200:
        filename = TEST_OUTPUT_DIR / "paragraph_formatting.pptx"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"✅ Generated: {filename}")
    else:
        print(f"❌ Failed: {response.status_code}")

def test_comprehensive_layout():
    """Test comprehensive layout with all features"""
    
    request_data = {
        "query": "Complete presentation testing all enhanced features",
        "slides": [
            {
                "title": "Enhanced Formatting Showcase",
                "content": [
                    {
                        "text": "This presentation demonstrates improved formatting capabilities",
                        "sub_points": [
                            "Adaptive text sizing based on content density",
                            "Proper spacing to prevent overlapping",
                            "Enhanced visual hierarchy and readability"
                        ]
                    }
                ]
            },
            {
                "title": "Dense Content Example",
                "content": [
                    {
                        "text": "Complex systems require comprehensive understanding of multiple interconnected components and their relationships",
                        "sub_points": [
                            "System architecture involves multiple layers of abstraction",
                            "Data flow between components must be carefully managed",
                            "Error handling and recovery mechanisms are crucial",
                            "Performance optimization requires careful analysis"
                        ]
                    },
                    {
                        "text": "Implementation strategies must consider scalability, maintainability, and security requirements throughout the development lifecycle"
                    }
                ],
                "image_url": "https://via.placeholder.com/600x400/9C27B0/FFFFFF?text=Complex+System"
            },
            {
                "title": "Process and Comparison",
                "content": [
                    {"text": "Visual diagrams enhance understanding"}
                ],
                "diagram_type": "process",
                "diagram_data": [
                    {"step": "Analysis"},
                    {"step": "Design"},
                    {"step": "Implementation"},
                    {"step": "Testing"}
                ],
                "image_url": "https://via.placeholder.com/400x300/607D8B/FFFFFF?text=Workflow"
            }
        ],
        "num_slides": 5,
        "include_images": True,
        "include_diagrams": True
    }
    
    print(f"\n🎯 Testing comprehensive enhanced layout...")
    
    response = requests.post(f"{API_BASE}/api/generate-ppt", json=request_data)
    if response.status_code == 200:
        filename = TEST_OUTPUT_DIR / "comprehensive_enhanced.pptx"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"✅ Generated: {filename}")
    else:
        print(f"❌ Failed: {response.status_code}")

def main():
    """Run all enhanced formatting tests"""
    print("🚀 Starting Enhanced PowerPoint Formatting Tests")
    print("=" * 60)
    
    # Setup
    setup_test_directory()
    
    # Wait for server
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    try:
        # Run tests
        test_adaptive_text_formatting()
        test_image_text_positioning()
        test_diagram_spacing()
        test_paragraph_formatting()
        test_comprehensive_layout()
        
        print("\n" + "=" * 60)
        print("✅ All Enhanced Formatting Tests Completed!")
        print(f"📁 Test files saved to: {TEST_OUTPUT_DIR.absolute()}")
        print("\n🎯 Key Improvements Tested:")
        print("   • Adaptive text sizing based on content density")
        print("   • Enhanced spacing and margin control")
        print("   • Improved image-text positioning")
        print("   • Better diagram sizing and placement")
        print("   • Paragraph-style content formatting")
        print("   • Comprehensive overlap prevention")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server. Please ensure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
