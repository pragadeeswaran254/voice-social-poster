import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { FaInstagram, FaTwitter, FaCopy, FaDownload, FaMicrophone, FaStop, FaPaperPlane, FaMagic, FaCalendarAlt, FaCheckCircle, FaClock } from "react-icons/fa";
import { SignedIn, SignedOut, SignIn, UserButton, useUser } from "@clerk/clerk-react";

function App() {
  const { user } = useUser()
  const [posts, setPosts] = useState([])
  const [content, setContent] = useState("")
  const [tone, setTone] = useState("Professional")
  const [status, setStatus] = useState("System Ready")
  const [isListening, setIsListening] = useState(false)
 
  const [scheduledTime, setScheduledTime] = useState("");
  const [isScheduling, setIsScheduling] = useState(false);

  const recognitionRef = useRef(null)

  const fetchPosts = async () => {
    if (!user) return;
    try {
      const apiUrl = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/posts` : "http://127.0.0.1:8000/posts";
      const response = await axios.get(`${apiUrl}?user_id=${user.id}`)
      setPosts(response.data)
    } catch (error) {
      setStatus("Error: Backend not connected")
    }
  }

  useEffect(() => {
    if (user) {
      fetchPosts()
      const interval = setInterval(fetchPosts, 10000);
      return () => clearInterval(interval);
    }
  }, [user])

  const handleTextSave = async () => {
    if (!content) return alert("Please speak or type something first!")
   
    const newPost = { user_id: user.id, content: content, tone: tone }
    setStatus(`✨ Generating ${tone} Magic... Please Wait ⏳`)
   
    try {
      const apiUrl = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/posts` : "http://127.0.0.1:8000/posts";
      await axios.post(apiUrl, newPost)
      setContent("")
      fetchPosts()
      setStatus("Content Generated! ✅")
    } catch (error) {
      alert("Failed to save.")
      setStatus("Error Saving.")
    }
  }

  const handleSchedulePost = async (postId) => {
    if (!scheduledTime) {
      alert("Please select a date and time first!");
      return;
    }
   
    setIsScheduling(true);
   
    try {
      const apiUrl = import.meta.env.VITE_API_URL
        ? `${import.meta.env.VITE_API_URL}/posts/${postId}/schedule`
        : `http://127.0.0.1:8000/posts/${postId}/schedule`;
     
      await axios.put(apiUrl, {
        scheduled_time: scheduledTime
      });

      alert(`Awesome! Post successfully scheduled for ${scheduledTime.replace("T", " ")} 🚀`);
      setScheduledTime("");
      fetchPosts(); 
     
    } catch (error) {
      console.error("Scheduling failed", error);
      alert("Failed to reach the database. Is your backend running?");
    } finally {
      setIsScheduling(false);
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
    <>
      {/* MODERN CSS INJECTION */}
      <style>{`
        body {
          background-color: #f3f4f6;
          background-image: radial-gradient(at 0% 0%, hsla(253,16%,7%,0.05) 0, transparent 50%), radial-gradient(at 50% 0%, hsla(225,39%,30%,0.05) 0, transparent 50%), radial-gradient(at 100% 0%, hsla(339,49%,30%,0.05) 0, transparent 50%);
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          color: #1f2937;
        }
        .glass-card {
          background: rgba(255, 255, 255, 0.9);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          border: 1px solid rgba(255, 255, 255, 0.5);
          border-radius: 24px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.04);
          overflow: hidden;
        }
        .gradient-text {
          background: linear-gradient(135deg, #4f46e5 0%, #ec4899 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          font-weight: 800;
        }
        .btn-hover {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .btn-hover:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        }
        .btn-hover:active {
          transform: translateY(0);
        }
        .modern-input {
          transition: border-color 0.3s, box-shadow 0.3s;
        }
        .modern-input:focus {
          outline: none;
          border-color: #4f46e5;
          box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.1);
        }
        .platform-card {
          transition: all 0.3s ease;
        }
        .platform-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 12px 24px rgba(0,0,0,0.06);
        }
      `}</style>

      <div style={{ padding: "40px 20px", maxWidth: "1000px", margin: "0 auto", minHeight: "100vh" }}>
       
        <SignedOut>
          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', padding: '40px' }}>
            <h1 className="gradient-text" style={{ fontSize: "3rem", marginBottom: "10px" }}>SocialFlow AI</h1>
            <p style={{ color: "#6b7280", marginBottom: "30px", fontSize: "1.2rem" }}>Your intelligent social media co-pilot.</p>
            <SignIn routing="hash" />
          </div>
        </SignedOut>

        <SignedIn>
          {/* HEADER */}
          <div className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: "20px 30px", marginBottom: "30px" }}>
            <h1 className="gradient-text" style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: 0, fontSize: "24px" }}>
              <FaMagic style={{ color: "#4f46e5" }} /> SocialFlow AI
            </h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
              <span style={{ fontSize: "14px", fontWeight: "600", color: status.includes("Error") ? "#ef4444" : status.includes("Wait") ? "#f59e0b" : "#10b981", backgroundColor: "rgba(0,0,0,0.03)", padding: "8px 16px", borderRadius: "20px" }}>
                {status}
              </span>
              <UserButton />
            </div>
          </div>

          {/* GENERATOR CARD */}
          <div className="glass-card" style={{ padding: "40px", marginBottom: "40px" }}>
            <h2 style={{ marginTop: 0, marginBottom: "25px", fontSize: "20px", color: "#111827", display: "flex", alignItems: "center", gap: "10px" }}>
              ✍️ What's on your mind?
            </h2>

            <button
              onClick={toggleListening}
              className="btn-hover"
              style={{
                width: "100%", padding: "16px", fontSize: "16px", fontWeight: "600", marginBottom: "20px", display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
                background: isListening ? "linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)" : "linear-gradient(135deg, #10b981 0%, #059669 100%)", 
                color: "white", border: "none", borderRadius: "16px", cursor: "pointer"
              }}>
              {isListening ? <><FaStop /> Stop Recording</> : <><FaMicrophone /> Click to Speak Your Idea</>}
            </button>

            <textarea
              className="modern-input"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="e.g., I just visited Mahabalipuram and the rock carvings were absolutely mind-blowing..."
              style={{ 
                width: "100%", height: "120px", padding: "20px", fontSize: "16px", borderRadius: "16px", 
                border: "2px solid #e5e7eb", marginBottom: "20px", boxSizing: "border-box", 
                color: "#1f2937", backgroundColor: "#f9fafb", resize: "none", lineHeight: "1.5"
              }}
            />

            <div style={{ display: "flex", gap: "20px", marginBottom: "25px" }}>
              <div style={{ flex: 1 }}>
                <label style={{ display: "block", fontWeight: "600", marginBottom: "10px", color: "#4b5563", fontSize: "14px" }}>Target Tone</label>
                <select
                  className="modern-input"
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                  style={{ 
                    width: "100%", padding: "14px", fontSize: "15px", borderRadius: "12px", 
                    border: "2px solid #e5e7eb", color: "#1f2937", backgroundColor: "#f9fafb", cursor: "pointer", fontWeight: "500"
                  }}
                >
                  <option value="Professional">👔 Professional & Corporate</option>
                  <option value="Funny">😂 Funny & Humorous</option>
                  <option value="Sarcastic">😒 Sarcastic & Witty</option>
                  <option value="Inspiring">✨ Inspiring & Motivational</option>
                  <option value="Gen Z">🔥 Gen Z Slang</option>
                </select>
              </div>
            </div>
           
            <button 
              onClick={handleTextSave} 
              className="btn-hover"
              style={{ 
                width: "100%", padding: "18px", background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)", 
                color: "white", border: "none", borderRadius: "16px", cursor: "pointer", fontSize: "16px", 
                fontWeight: "bold", display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' 
              }}>
                <FaPaperPlane /> Generate High-Converting Post
            </button>
          </div>

          {/* GENERATED POSTS FEED */}
          <div style={{ display: "flex", flexDirection: "column", gap: "40px" }}>
            {posts.map((post, index) => {
             
              const ignoreWords = ["today", "went", "want", "just", "like", "with", "this", "that", "the", "and", "for", "from"];
              const searchKeywords = post.content
                .toLowerCase()
                .replace(/[^a-z ]/g, "")
                .split(" ")
                .filter(word => word.length > 2 && !ignoreWords.includes(word))
                .slice(0, 2)
                .join(",");

              let imageUrl = post.is_upload ? `data:image/jpeg;base64,${post.image_data}` : `https://loremflickr.com/800/800/${searchKeywords}?lock=${post.image_seed}`;

              return (
                <div key={index} className="glass-card" style={{ display: "flex", flexDirection: "column" }}>
                 
                  {/* Post Header / Status Bar */}
                  <div style={{ padding: "20px 30px", borderBottom: "1px solid #f3f4f6", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px", backgroundColor: "#ffffff" }}>
                    <span style={{ color: "#4b5563", fontSize: "15px" }}>
                      <strong style={{ color: "#111827" }}>Topic:</strong> "{post.content}"
                    </span>
                    <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                      {post.tone && <span style={{ backgroundColor: "#f3f4f6", color: "#4f46e5", padding: "6px 14px", borderRadius: "20px", fontSize: "12px", fontWeight: "bold" }}>{post.tone} Tone</span>}
                     
                      {post.status === "Scheduled" && (
                        <span style={{ backgroundColor: "#fef3c7", color: "#d97706", padding: "6px 14px", borderRadius: "20px", fontSize: "12px", fontWeight: "bold", display: "flex", alignItems: "center", gap: "5px" }}>
                          <FaClock /> Scheduled
                        </span>
                      )}
                     
                      {post.status === "Published" && (
                        <span style={{ backgroundColor: "#d1fae5", color: "#059669", padding: "6px 14px", borderRadius: "20px", fontSize: "12px", fontWeight: "bold", display: "flex", alignItems: "center", gap: "5px" }}>
                          <FaCheckCircle /> Published
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Image Section */}
                  <div style={{ width: "100%", height: "450px", overflow: "hidden", backgroundColor: "#f9fafb", position: "relative" }}>
                    <img
                      src={imageUrl}
                      alt="Theme Visual"
                      style={{ width: "100%", height: "100%", objectFit: "cover" }}
                    />
                    <button
                      onClick={() => handleDownload(imageUrl)}
                      className="btn-hover"
                      title="Download Image"
                      style={{
                        position: "absolute", bottom: "20px", right: "20px",
                        backgroundColor: "rgba(255,255,255,0.9)", backdropFilter: "blur(4px)", padding: "14px", borderRadius: "50%",
                        display: "flex", alignItems: "center", justifyContent: "center",
                        boxShadow: "0 4px 15px rgba(0,0,0,0.1)", cursor: "pointer", color: "#111827", border: "none"
                      }}
                    >
                      <FaDownload size={20} />
                    </button>
                  </div>
                 
                  {/* Platforms Grid */}
                  <div style={{ display: "flex", gap: "25px", padding: "30px", flexDirection: "row", flexWrap: "wrap", backgroundColor: "#ffffff" }}>
                   
                    {/* Instagram Box */}
                    <div className="platform-card" style={{ flex: 1, minWidth: "300px", borderRadius: "20px", padding: "25px", backgroundColor: "#fdf2f8", position: "relative", border: "1px solid #fce7f3" }}>
                      <h4 style={{ color: "#db2777", margin: "0 0 20px 0", display: 'flex', alignItems: 'center', gap: '10px', fontSize: "18px" }}>
                        <FaInstagram size={22} /> Instagram Caption
                      </h4>
                      <p style={{ whiteSpace: "pre-wrap", marginBottom: "40px", color: "#374151", lineHeight: "1.7", fontSize: "15px" }}>{post.instagram_version}</p>
                     
                      <button
                        onClick={() => copyToClipboard(post.instagram_version)}
                        className="btn-hover"
                        style={{ position: "absolute", bottom: "20px", right: "20px", backgroundColor: "white", border: "1px solid #fbcfe8", padding: "8px 16px", borderRadius: "12px", cursor: "pointer", color: "#db2777", display: 'flex', alignItems: 'center', gap: '8px', fontWeight: "600" }}
                      >
                        <FaCopy /> Copy
                      </button>
                    </div>

                    {/* Twitter Box */}
                    <div className="platform-card" style={{ flex: 1, minWidth: "300px", borderRadius: "20px", padding: "25px", backgroundColor: "#f0f9ff", position: "relative", border: "1px solid #e0f2fe" }}>
                      <h4 style={{ color: "#0284c7", margin: "0 0 20px 0", display: 'flex', alignItems: 'center', gap: '10px', fontSize: "18px" }}>
                        <FaTwitter size={22} /> Twitter Version
                      </h4>
                      <p style={{ whiteSpace: "pre-wrap", marginBottom: "40px", color: "#374151", lineHeight: "1.7", fontSize: "15px" }}>{post.twitter_version}</p>
                     
                      <button
                        onClick={() => copyToClipboard(post.twitter_version)}
                        className="btn-hover"
                        style={{ position: "absolute", bottom: "20px", right: "20px", backgroundColor: "white", border: "1px solid #bae6fd", padding: "8px 16px", borderRadius: "12px", cursor: "pointer", color: "#0284c7", display: 'flex', alignItems: 'center', gap: '8px', fontWeight: "600" }}
                      >
                        <FaCopy /> Copy
                      </button>
                    </div>

                  </div>

                  {/* Smart Scheduling UI */}
                  {(!post.status || post.status === "Generated") && (
                    <div style={{ margin: "0 30px 30px 30px", padding: "25px", backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "20px" }}>
                      <h3 style={{ fontSize: "18px", fontWeight: "700", color: "#1e293b", margin: "0 0 8px 0", display: "flex", alignItems: "center", gap: "10px" }}>
                        <FaCalendarAlt color="#64748b" /> Schedule Automation
                      </h3>
                      <p style={{ fontSize: "14px", color: "#64748b", marginBottom: "20px", marginTop: 0 }}>
                        Select when you want our AI engine to automatically beam this content to Telegram and your Web App.
                      </p>
                     
                      <div style={{ display: "flex", gap: "15px", alignItems: "center", flexWrap: "wrap" }}>
                        <input
                          className="modern-input"
                          type="datetime-local"
                          style={{ 
                            padding: "16px", border: "2px solid #e2e8f0", borderRadius: "14px", flex: "1", 
                            minWidth: "200px", fontSize: "15px", color: "#1e293b", backgroundColor: "white", 
                            cursor: "pointer", fontWeight: "500"
                          }}
                          value={scheduledTime}
                          onChange={(e) => setScheduledTime(e.target.value)}
                          onClick={(e) => e.target.showPicker && e.target.showPicker()}
                        />
                        <button
                          className="btn-hover"
                          style={{
                            backgroundColor: (scheduledTime && !isScheduling) ? "#10b981" : "#cbd5e1",
                            color: "white", fontWeight: "bold", padding: "16px 32px",
                            borderRadius: "14px", border: "none", fontSize: "16px",
                            cursor: (scheduledTime && !isScheduling) ? "pointer" : "not-allowed",
                            display: "flex", alignItems: "center", gap: "10px"
                          }}
                          onClick={() => handleSchedulePost(post.id)}
                          disabled={!scheduledTime || isScheduling}
                        >
                          {isScheduling ? "Saving..." : <>Schedule Post 🚀</>}
                        </button>
                      </div>
                    </div>
                  )}

                  {post.status === "Scheduled" && (
                    <div style={{ margin: "0 30px 30px 30px", padding: "20px", backgroundColor: "#fef3c7", borderRadius: "16px", textAlign: "center", border: "1px solid #fde68a" }}>
                      <p style={{ margin: 0, color: "#b45309", fontWeight: "600", fontSize: "15px", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
                        <FaClock /> This post is securely queued in the background worker to publish at {post.scheduled_time.replace("T", " ")}
                      </p>
                    </div>
                  )}

                  {post.status === "Published" && (
                    <div style={{ margin: "0 30px 30px 30px", padding: "20px", backgroundColor: "#d1fae5", borderRadius: "16px", textAlign: "center", border: "1px solid #a7f3d0" }}>
                      <p style={{ margin: 0, color: "#047857", fontWeight: "600", fontSize: "15px", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
                        <FaCheckCircle /> Automation Complete! Payload delivered to external channels.
                      </p>
                    </div>
                  )}

                </div>
              )
            })}
          </div>
        </SignedIn>
      </div>
    </>
  )
}

export default App