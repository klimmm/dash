// Add this to your assets/js/table-scroll.js
document.addEventListener('DOMContentLoaded', function() {
    const tableWrappers = document.querySelectorAll('.data-table-wrapper');
    
    tableWrappers.forEach(wrapper => {
        const handleScroll = () => {
            const isScrollable = wrapper.scrollWidth > wrapper.clientWidth;
            const isStart = wrapper.scrollLeft > 0;
            const isEnd = wrapper.scrollLeft + wrapper.clientWidth < wrapper.scrollWidth;
            
            wrapper.classList.toggle('scroll-start', isStart && isScrollable);
            wrapper.classList.toggle('scroll-end', isEnd && isScrollable);
        };
        
        wrapper.addEventListener('scroll', handleScroll);
        window.addEventListener('resize', handleScroll);
        handleScroll(); // Initial check
    });
});