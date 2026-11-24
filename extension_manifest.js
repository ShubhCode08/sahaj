{
  "manifest_version": 3,
  "name": "Sahaj MVP",
  "version": "1.0",
  "permissions": [
    "activeTab",
    "scripting"
  ],
  "action": {
    "default_popup": "popup.html"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content.js"]
    }
  ]
}
