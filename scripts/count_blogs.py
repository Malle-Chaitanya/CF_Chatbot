"""
Script to count how many blog posts are in the vector database.
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def count_blogs_in_vectorstore():
    """Count blog posts in the vector database."""
    print("=" * 60)
    print("BLOG COUNT IN VECTOR DATABASE")
    print("=" * 60)
    
    try:
        # Try to use existing vectorstore from app.vectorstore
        print("[*] Loading vectorstore from app.vectorstore...")
        from app.vectorstore import vectorstore
        
        if not vectorstore:
            print("[ERROR] Vectorstore is not initialized")
            print("[INFO] Set INITIALIZE_VECTORSTORE=true in environment to initialize")
            return None
        
        # Get total document count
        total_docs = vectorstore._collection.count()
        print(f"[OK] Total documents in vectorstore: {total_docs}")
        
        # Get all documents with metadata to filter blogs
        print("[*] Analyzing documents to identify blogs...")
        try:
            all_data = vectorstore.get(include=["metadatas", "documents"])
        except Exception as e:
            print(f"[WARNING] Could not fetch all data: {e}")
            print("[INFO] Trying alternative method...")
            # Try to get a sample and estimate
            sample_docs = vectorstore.similarity_search("blog", k=1000)
            all_data = {
                "metadatas": [doc.metadata for doc in sample_docs],
                "documents": [doc.page_content for doc in sample_docs]
            }
        
        metadatas = all_data.get("metadatas", [])
        documents = all_data.get("documents", [])
        
        # Count blogs by checking metadata
        blog_chunks = []
        unique_blog_posts = set()
        blog_metadata = []
        
        for i, metadata in enumerate(metadatas):
            if not metadata:
                continue
            
            # Check various blog indicators
            is_blog = False
            post_url = None
            post_title = None
            
            # Method 1: Check is_blog_post flag
            if metadata.get("is_blog_post") == True:
                is_blog = True
                post_url = metadata.get("post_url", "")
                post_title = metadata.get("post_title", "")
            
            # Method 2: Check source_type and tag
            elif metadata.get("source_type") == "web" or metadata.get("source") == "cloudfuze_blog":
                if metadata.get("tag") == "blog" or "blog" in str(metadata.get("source", "")).lower():
                    is_blog = True
                    post_url = metadata.get("post_url", "")
                    post_title = metadata.get("post_title", "")
            
            # Method 3: Check if URL contains cloudfuze.com
            elif "cloudfuze.com" in str(metadata.get("post_url", "")):
                is_blog = True
                post_url = metadata.get("post_url", "")
                post_title = metadata.get("post_title", "")
            
            if is_blog:
                blog_chunks.append(i)
                if post_url:
                    unique_blog_posts.add(post_url)
                blog_metadata.append({
                    "title": post_title or "Unknown",
                    "url": post_url or "Unknown",
                    "chunk_index": i
                })
        
        print(f"\n[RESULTS]")
        print(f"  Total documents (chunks): {total_docs}")
        print(f"  Blog chunks: {len(blog_chunks)}")
        print(f"  Unique blog posts: {len(unique_blog_posts)}")
        print(f"  Blog chunks percentage: {(len(blog_chunks)/total_docs*100):.1f}%")
        
        # Show some sample blog posts
        if blog_metadata:
            print(f"\n[SAMPLE BLOG POSTS] (showing first 10)")
            for i, blog in enumerate(blog_metadata[:10], 1):
                print(f"  {i}. {blog['title']}")
                print(f"     URL: {blog['url']}")
        
        # Count by source type breakdown
        print(f"\n[SOURCE BREAKDOWN]")
        source_counts = {}
        for metadata in metadatas:
            if not metadata:
                continue
            source = metadata.get("source_type", metadata.get("source", "unknown"))
            source_counts[source] = source_counts.get(source, 0) + 1
        
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count} chunks")
        
        return {
            "total_documents": total_docs,
            "blog_chunks": len(blog_chunks),
            "unique_blog_posts": len(unique_blog_posts),
            "blog_percentage": (len(blog_chunks)/total_docs*100) if total_docs > 0 else 0
        }
        
    except FileNotFoundError:
        print(f"[ERROR] Vectorstore not found at {CHROMA_DB_PATH}")
        print("[INFO] Vectorstore may not have been initialized yet.")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to count blogs: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = count_blogs_in_vectorstore()
    if result:
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Unique blog posts in vector database: {result['unique_blog_posts']}")
        print(f"Blog chunks in vector database: {result['blog_chunks']}")
        print("=" * 60)

