import { useEffect } from "react";

const GoogleTag = () => {
  useEffect(() => {
    // Check if script already exists to avoid duplicates
    const scriptId = "google-tag-manager";
    if (document.getElementById(scriptId)) return;

    // Load gtag.js
    const script = document.createElement("script");
    script.id = scriptId;
    script.async = true;
    script.src = "https://www.googletagmanager.com/gtag/js?id=G-EP2L8DXXLJ";
    document.head.appendChild(script);

    // Initialize gtag
    const inlineScript = document.createElement("script");
    inlineScript.innerHTML = `
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-EP2L8DXXLJ');
    `;
    document.head.appendChild(inlineScript);

    return () => {
      // Optional: Cleanup scripts when component unmounts if strictly needed for SPAs
      // However, usually Google Tag persists across the session.
    };
  }, []);

  return null;
};

export default GoogleTag;
