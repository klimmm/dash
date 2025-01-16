window.addEventListener('load', function() {
    function updateSize() {
        const debugEl = document.getElementById('window-size-debug');
        if (debugEl) {
            debugEl.textContent = `Window: ${window.innerWidth}px × ${window.innerHeight}px`;
        }
    }
    window.addEventListener('resize', updateSize);
    updateSize();
});


// Add to your app's JavaScript
function debugWidthConstraints() {
    const elements = document.querySelectorAll('*');
    elements.forEach(el => {
        const style = window.getComputedStyle(el);
        const width = parseFloat(style.width);
        if (width > 700) {  // Adjust threshold as needed
            console.log('Wide element:', {
                element: el,
                width: width,
                minWidth: style.minWidth,
                maxWidth: style.maxWidth,
                className: el.className
            });
        }
    });
}

// Call on resize
window.addEventListener('resize', debounce(debugWidthConstraints, 250));


// Find elements preventing resize
function findFixedWidthElements() {
    const all = document.getElementsByTagName('*');
    for (const el of all) {
        const style = window.getComputedStyle(el);
        const width = parseFloat(style.width);
        const minWidth = parseFloat(style.minWidth);
        
        if (width > 700 || minWidth > 700) {
            console.log('Problem element:', {
                element: el,
                width: style.width,
                minWidth: style.minWidth,
                className: el.className
            });
        }
    }
}

// Run on resize
let timeout;
window.addEventListener('resize', () => {
    clearTimeout(timeout);
    timeout = setTimeout(findFixedWidthElements, 100);
});

// Run on load
window.addEventListener('load', findFixedWidthElements);