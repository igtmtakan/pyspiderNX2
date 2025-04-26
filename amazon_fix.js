// Amazon Fix for PySpider
// This script defines missing functions in Amazon pages to prevent errors

// Define markFeatureRenderForImageBlock function if not exists
if (typeof window.markFeatureRenderForImageBlock === 'undefined') {
    window.markFeatureRenderForImageBlock = function() {
        console.log('Mock markFeatureRenderForImageBlock called');
        return true;
    };
}

// Define other potentially missing Amazon functions
if (typeof window.P === 'undefined') {
    window.P = {
        register: function() { return {}; },
        execute: function() { return {}; },
        when: function() { return { execute: function() {} }; }
    };
}

// Define jQuery if not exists (some Amazon pages expect it)
if (typeof window.jQuery === 'undefined') {
    window.jQuery = function() { 
        return {
            on: function() { return this; },
            ready: function(fn) { setTimeout(fn, 0); return this; }
        };
    };
    window.$ = window.jQuery;
}

console.log('Amazon fix script loaded successfully');
