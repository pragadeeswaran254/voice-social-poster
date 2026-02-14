import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { FaInstagram, FaTwitter, FaCopy, FaDownload, FaMicrophone, FaStop, FaCamera, FaPaperPlane } from "react-icons/fa";

function App() {
  const [posts, setPosts] = useState([])
  const [content, setContent] = useState("")
  const [tone, setTone] = useState("Professional") 
  const [status, setStatus] = useState("System Ready")
  const [isListening, setIsListening] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null) // <--- NEW STATE FOR IMAGE
  
  const recognitionRef = useRef(null)
  const fileInputRef = useRef(null) // Reference to the hidden file input

  const fetchPosts = async () => {
    try {
      const response = await axios.get("http://127.0.0.1:8000/posts")
      setPosts(response.data)
    } catch (error) {
      setStatus("Error: Backend not connected")
    }
  }

  useEffect(() => { fetchPosts() }, [])

  // --- HANDLER FOR TEXT POSTS ---
  const handleTextSave = async () => {
    if (!content) return alert("Please speak or type something first!")
    
    const newPost = { content: content, tone: tone }
    setStatus(`Generating ${tone} Content... Please Wait ⏳`)
    
    try {
      await axios.post("http://127.0.0.1:8000/posts", newPost)
      setContent("")
      fetchPosts()
      setStatus("Content Generated! ✅")
    } catch (error) { 
      alert("Failed to save.") 
      setStatus("Error Saving.")
    }
  }

  // --- NEW: HANDLER FOR IMAGE UPLOADS ---
  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setStatus(`Uploading & Analyzing Image... 📸`)
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("tone", tone);

    try {
      await axios.post("http://127.0.0.1:8000/upload-image", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      fetchPosts();
      setStatus("Vision Analysis Complete! ✅");
      setSelectedFile(null); // Reset
    } catch (error) {
      console.error(error);
      setStatus("Error Uploading Image.");
      alert("Upload failed.");
    }
  };

  const toggleListening = () => {
    if (isListening) {
      if (recognitionRef.current) recognitionRef.current.stop()
      setIsListening(false)
      setStatus("Stopped manually.")
      return
    }

    if (!('webkitSpeechRecognition' in window)) return alert("Use Chrome!")
    
    const recognition = new window.webkitSpeechRecognition()
    recognitionRef.current = recognition
    recognition.lang = 'en-US'
    recognition.continuous = false 

    setIsListening(true)
    setStatus("Listening... Click again to Stop 🛑")
    recognition.start()

    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript
      setContent(transcript)
      setIsListening(false)
      setStatus("Voice captured! ✅")
    }
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setStatus("Copied to clipboard! 📋"); 
    setTimeout(() => setStatus("System Ready"), 2000);
  }

  const handleDownload = async (imageUrl) => {
    try {
        // If it's a base64 image (uploaded by user), download it differently
        if (imageUrl.startsWith("data:image")) {
            const link = document.createElement('a');
            link.href = imageUrl;
            link.download = `my-upload-${Date.now()}.jpg`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            setStatus("Image Downloaded! 📸");
            return;
        }

        // Standard Download logic for Web Images
        const response = await fetch(imageUrl);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `social-post-${Date.now()}.jpg`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        setStatus("Image Downloaded! 📸");
    } catch (error) {
        console.error("Download failed:", error);
        window.open(imageUrl, '_blank');
    }
  }

  return (
    <div style={{ padding: "40px", fontFamily: "Arial", maxWidth: "900px", margin: "0 auto", backgroundColor: "#fafafa", minHeight: "100vh" }}>
      <h1 style={{ textAlign: "center", color: "#333", display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
        🎙️ AI Social Manager + 📸
      </h1>
      
      {/* Status Bar */}
      <div style={{ padding: "10px", backgroundColor: "#e1e1e1", marginBottom: "20px", borderRadius: "5px", textAlign: "center" }}>
        <strong>Status:</strong> {status}
      </div>

      {/* Input Section */}
      <div style={{ backgroundColor: "white", padding: "30px", borderRadius: "15px", boxShadow: "0 4px 15px rgba(0,0,0,0.1)" }}>
        
        {/* Voice Button */}
        <button 
          onClick={toggleListening}
          style={{ 
            width: "100%", padding: "15px", fontSize: "18px", marginBottom: "15px", display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
            backgroundColor: isListening ? "#ff4757" : "#2ed573", color: "white", border: "none", borderRadius: "10px", cursor: "pointer" 
          }}>
          {isListening ? <><FaStop /> Stop Listening</> : <><FaMicrophone /> Click to Speak Your Idea</>}
        </button>

        <textarea 
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Example: I just built a cool robot using Arduino..."
          style={{ width: "100%", height: "80px", padding: "15px", fontSize: "16px", borderRadius: "10px", border: "1px solid #ddd", marginBottom: "15px", boxSizing: "border-box" }}
        />

        <div style={{ marginBottom: "20px" }}>
          <label style={{ fontWeight: "bold", marginRight: "10px" }}>Select Tone:</label>
          <select 
            value={tone} 
            onChange={(e) => setTone(e.target.value)}
            style={{ padding: "10px", fontSize: "16px", borderRadius: "8px", border: "1px solid #ddd", width: "100%", marginTop: "5px" }}
          >
            <option value="Professional">👔 Professional & Corporate</option>
            <option value="Funny">😂 Funny & Humorous</option>
            <option value="Sarcastic">😒 Sarcastic & Witty</option>
            <option value="Inspiring">✨ Inspiring & Motivational</option>
            <option value="Gen Z">🔥 Gen Z Slang</option>
          </select>
        </div>
        
        {/* --- DUAL BUTTONS: TEXT OR IMAGE --- */}
        <div style={{ display: "flex", gap: "10px" }}>
            {/* 1. Generate from Text Button */}
            <button onClick={handleTextSave} style={{ flex: 1, padding: "15px", backgroundColor: "#3742fa", color: "white", border: "none", borderRadius: "10px", cursor: "pointer", fontSize: "16px", fontWeight: "bold", display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
                <FaPaperPlane /> Generate from Text
            </button>

            {/* 2. Upload Image Button */}
            <input 
                type="file" 
                accept="image/*" 
                ref={fileInputRef} 
                style={{ display: "none" }} 
                onChange={handleImageUpload} 
            />
            <button 
                onClick={() => fileInputRef.current.click()} 
                style={{ flex: 1, padding: "15px", backgroundColor: "#e67e22", color: "white", border: "none", borderRadius: "10px", cursor: "pointer", fontSize: "16px", fontWeight: "bold", display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
                <FaCamera /> Upload Photo
            </button>
        </div>

      </div>

      {/* Results Section */}
      <div style={{ marginTop: "40px" }}>
        {posts.map((post, index) => {
          
          const ignoreWords = ["today", "went", "want", "just", "like", "with", "this", "that", "the", "and", "for", "from"];
          const searchKeywords = post.content
            .toLowerCase()
            .replace(/[^a-z ]/g, "")
            .split(" ")
            .filter(word => word.length > 2 && !ignoreWords.includes(word))
            .slice(0, 2)
            .join(",");

          // --- LOGIC: If uploaded, use Base64. If text, use LoremFlickr. ---
          let imageUrl = "";
          if (post.is_upload) {
             imageUrl = `data:image/jpeg;base64,${post.image_data}`;
          } else {
             imageUrl = `https://loremflickr.com/800/800/${searchKeywords}?lock=${post.image_seed}`;
          }

          return (
            <div key={index} style={{ marginBottom: "30px", backgroundColor: "white", borderRadius: "15px", overflow: "hidden", boxShadow: "0 4px 10px rgba(0,0,0,0.05)" }}>
              
              <div style={{ width: "100%", height: "400px", overflow: "hidden", backgroundColor: "#000", position: "relative" }}>
                <img 
                  src={imageUrl}
                  alt="Theme Visual"
                  style={{ width: "100%", height: "100%", objectFit: "contain" }} 
                />
                
                <button 
                  onClick={() => handleDownload(imageUrl)}
                  title="Download Image"
                  style={{
                    position: "absolute", bottom: "15px", right: "15px",
                    backgroundColor: "white", padding: "10px", borderRadius: "50%",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    boxShadow: "0 2px 10px rgba(0,0,0,0.3)", cursor: "pointer", color: "#333", border: "none"
                  }}
                >
                  <FaDownload size={20} />
                </button>
              </div>

              <div style={{ padding: "15px", backgroundColor: "#f1f2f6", borderBottom: "1px solid #eee", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span><strong>Your Topic:</strong> "{post.content}"</span>
                {post.tone && <span style={{ backgroundColor: "#3742fa", color: "white", padding: "4px 10px", borderRadius: "12px", fontSize: "12px" }}>{post.tone} Tone</span>}
              </div>
              
              <div style={{ display: "flex", gap: "20px", padding: "20px", flexDirection: "row", flexWrap: "wrap" }}>
                
                <div style={{ flex: 1, minWidth: "300px", border: "1px solid #e1306c", borderRadius: "10px", padding: "15px", backgroundColor: "#fff5f8", position: "relative" }}>
                  <h4 style={{ color: "#e1306c", marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FaInstagram /> Instagram Caption
                  </h4>
                  <p style={{ whiteSpace: "pre-wrap", marginBottom: "30px" }}>{post.instagram_version}</p>
                  
                  <button 
                    onClick={() => copyToClipboard(post.instagram_version)}
                    style={{ position: "absolute", bottom: "10px", right: "10px", background: "none", border: "none", cursor: "pointer", color: "#e1306c", display: 'flex', alignItems: 'center', gap: '5px' }}
                  >
                    <FaCopy /> Copy
                  </button>
                </div>

                <div style={{ flex: 1, minWidth: "300px", border: "1px solid #1da1f2", borderRadius: "10px", padding: "15px", backgroundColor: "#f0f8fd", position: "relative" }}>
                  <h4 style={{ color: "#1da1f2", marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FaTwitter /> Twitter Version
                  </h4>
                  <p style={{ whiteSpace: "pre-wrap", marginBottom: "30px" }}>{post.twitter_version}</p>
                  
                  <button 
                    onClick={() => copyToClipboard(post.twitter_version)}
                    style={{ position: "absolute", bottom: "10px", right: "10px", background: "none", border: "none", cursor: "pointer", color: "#1da1f2", display: 'flex', alignItems: 'center', gap: '5px' }}
                  >
                    <FaCopy /> Copy
                  </button>
                </div>

              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default App