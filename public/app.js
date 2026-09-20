// Force no-cache for all fetch requests
const CACHE_BUST = '?nocache=' + Date.now();

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        const tabId = tab.dataset.tab;
        document.getElementById(tabId).classList.add('active');
    });
});

// Clear input
function clearInput(inputId) {
    document.getElementById(inputId).value = '';
}

// Close format panel
function closeFormatPanel() {
    document.getElementById('formatPanel').style.display = 'none';
}

// Handle download button click
async function handleDownload(platform) {
    const urlInput = document.getElementById(`${platform}Url`);
    let rawUrl = urlInput.value.trim();
    
    if (!rawUrl) {
        alert('Please enter a valid URL');
        return;
    }

    // Auto-extract URL if user pasted extra text (e.g. "Video Title | https://...")
    const urlMatch = rawUrl.match(/https?:\/\/[^\s<>"{}|\\^`\[\]]+/i);
    if (urlMatch) {
        rawUrl = urlMatch[0];
        // Update the input field so only the clean URL remains
        urlInput.value = rawUrl;
    }
    
    if (!rawUrl.startsWith('http')) {
        alert('Please enter a valid URL starting with http:// or https://');
        return;
    }

    document.getElementById('loadingState').style.display = 'block';
    document.getElementById('formatPanel').style.display = 'none';

    try {
        const response = await fetch('/api/formats' + CACHE_BUST, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            },
            body: JSON.stringify({ url: rawUrl })
        });

        const data = await response.json();
        
        if (response.ok && data.formats) {
            displayFormats(data.formats);
        } else {
            const platform = document.querySelector('.tab.active').dataset.tab;
            let msg = 'Failed to fetch video formats. Please check the URL and try again.';
            if (data.details) {
                msg += '\n\nDetails: ' + data.details.substring(0, 300);
            }
            if (platform === 'bilibili') {
                msg = 'Bilibili format check failed.\n' + (data.details ? 'Details: ' + data.details.substring(0, 200) : 'Please check the URL is valid.');
            }
            alert(msg);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Connection error. Please make sure the server is running.');
    } finally {
        document.getElementById('loadingState').style.display = 'none';
    }
}

// Display format options
function displayFormats(formats) {
    console.log('[SaveAll v5] Received', formats.length, 'formats from API');
    
    // Debug: log raw data
    console.log('[SaveAll v5] Raw formats:', JSON.stringify(formats, null, 2));
    
    const container = document.getElementById('formatOptions');
    if (!container) {
        console.error('[SaveAll v5] ERROR: formatOptions container not found!');
        return;
    }
    
    container.innerHTML = '';

    let videoCount = 0;
    let audioCount = 0;

    formats.forEach((format, index) => {
        const option = document.createElement('div');
        option.className = 'format-option';
        
        // Check if this is an audio-only format
        const resText = (format.resolution || '').toLowerCase();
        const isAudioOnly = resText.includes('audio') || resText.includes('m4a only') || resText.includes('mp3 only');
        
        if (isAudioOnly) {
            audioCount++;
        } else {
            videoCount++;
        }
        
        console.log(`[SaveAll v5] Format ${index}: resolution="${format.resolution}" ext="${format.extension}" isAudio=${isAudioOnly}`);
        
        const badgeClass = isAudioOnly ? 'audio' : '';
        
        option.innerHTML = `
            <div class="format-info">
                <span class="format-badge ${badgeClass}">${format.extension}</span>
                <div>
                    <div class="format-resolution">${format.resolution}</div>
                    <div class="format-ext">${format.format_id}</div>
                </div>
            </div>
            <button class="format-download-btn" onclick="downloadVideo('${format.format_id}', '${format.extension}')">
                Download
            </button>
        `;
        
        container.appendChild(option);
    });

    console.log(`[SaveAll v5] Final: ${videoCount} video formats, ${audioCount} audio formats`);
    document.getElementById('formatPanel').style.display = 'block';
}

// Download video with selected format
async function downloadVideo(formatId, extension) {
    const activeTab = document.querySelector('.tab.active').dataset.tab;
    const urlInput = document.getElementById(`${activeTab}Url`);
    let rawUrl = urlInput.value.trim();

    // Auto-extract URL if user pasted extra text
    const urlMatch = rawUrl.match(/https?:\/\/[^\s<>"{}|\\^`\[\]]+/i);
    if (urlMatch) {
        rawUrl = urlMatch[0];
        urlInput.value = rawUrl;
    }

    if (!rawUrl.startsWith('http')) {
        alert('No valid URL found. Please paste a video URL first.');
        return;
    }

    const btn = event.target;
    const originalText = btn.textContent;
    btn.textContent = 'Downloading...';
    btn.disabled = true;

    try {
        const response = await fetch('/api/download' + CACHE_BUST, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            },
            body: JSON.stringify({ 
                url: rawUrl, 
                format: extension,
                quality: formatId 
            })
        });

        const data = await response.json();
        
        if (response.ok && data.success) {
            window.location.href = data.path;
            
            setTimeout(() => {
                const sizeMB = (data.file_size / (1024 * 1024)).toFixed(1);
                alert(`Saving "${data.filename}" (${sizeMB} MB)\n\nTo change where files are saved:\n• Edge/Chrome: Settings > Downloads > Change\n• Firefox: Settings > General > Downloads > Always ask you`);
            }, 500);
        } else {
            alert('Download failed: ' + (data.error || 'Unknown error'));
            if (data.details) {
                console.error('Server details:', data.details);
            }
        }
    } catch (error) {
        console.error('Download error:', error);
        alert('Download error. Please try again.');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

// Enter key support for inputs
document.getElementById('youtubeUrl').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleDownload('youtube');
});

document.getElementById('facebookUrl').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleDownload('facebook');
});

document.getElementById('bilibiliUrl').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleDownload('bilibili');
});
