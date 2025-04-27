// Amazon Map Polyfill for PySpider
// This script adds a polyfill for the Map object if it doesn't exist

// Map polyfill
if (typeof Map === 'undefined') {
    console.log('Adding Map polyfill for Amazon scraping');

    // Simple Map polyfill
    window.Map = function() {
        this.items = {};
        this.size = 0;
    };

    window.Map.prototype.set = function(key, value) {
        if (!this.has(key)) {
            this.size++;
        }
        this.items[key] = value;
        return this;
    };

    window.Map.prototype.get = function(key) {
        return this.has(key) ? this.items[key] : undefined;
    };

    window.Map.prototype.has = function(key) {
        return Object.prototype.hasOwnProperty.call(this.items, key);
    };

    window.Map.prototype.delete = function(key) {
        if (this.has(key)) {
            delete this.items[key];
            this.size--;
            return true;
        }
        return false;
    };

    window.Map.prototype.clear = function() {
        this.items = {};
        this.size = 0;
    };

    window.Map.prototype.forEach = function(callback, thisArg) {
        for (var key in this.items) {
            if (this.has(key)) {
                callback.call(thisArg, this.items[key], key, this);
            }
        }
    };

    window.Map.prototype.keys = function() {
        var keys = [];
        for (var key in this.items) {
            if (this.has(key)) {
                keys.push(key);
            }
        }
        return {
            next: function() {
                return {
                    done: keys.length === 0,
                    value: keys.shift()
                };
            },
            [Symbol.iterator]: function() { return this; }
        };
    };

    window.Map.prototype.values = function() {
        var values = [];
        for (var key in this.items) {
            if (this.has(key)) {
                values.push(this.items[key]);
            }
        }
        return {
            next: function() {
                return {
                    done: values.length === 0,
                    value: values.shift()
                };
            },
            [Symbol.iterator]: function() { return this; }
        };
    };

    window.Map.prototype.entries = function() {
        var entries = [];
        for (var key in this.items) {
            if (this.has(key)) {
                entries.push([key, this.items[key]]);
            }
        }
        return {
            next: function() {
                return {
                    done: entries.length === 0,
                    value: entries.shift()
                };
            },
            [Symbol.iterator]: function() { return this; }
        };
    };

    window.Map.prototype[Symbol.iterator] = window.Map.prototype.entries;
}

// Fix for P13NSCCards__p13n-desktop-carousel error
if (typeof window.P === 'undefined') {
    window.P = {
        register: function() { return {}; },
        execute: function() { return {}; },
        when: function() { return { execute: function() {} }; }
    };
}

// Fix for other potential Amazon-specific objects
if (typeof window.markFeatureRenderForImageBlock === 'undefined') {
    window.markFeatureRenderForImageBlock = function() {
        console.log('Mock markFeatureRenderForImageBlock called');
        return true;
    };
}

// Fix for csa function
if (typeof window.csa === 'undefined') {
    window.csa = function() {
        console.log('Mock csa function called');
        return {
            emit: function() { return {}; },
            register: function() { return {}; },
            getInstance: function() { return window.csa; }
        };
    };
}

// Make csa a constructor as well
window.csa.prototype = {};
window.csa.toString = function() { return "function csa() { [native code] }"; };

// Fix for CSA on any object
window.addEventListener('load', function() {
    // Find all objects and add csa if needed
    for (var prop in window) {
        if (window.hasOwnProperty(prop) && typeof window[prop] === 'object' && window[prop] !== null) {
            if (typeof window[prop].csa === 'undefined') {
                window[prop].csa = window.csa;
            }
        }
    }
});

// Fix for Set object if needed
if (typeof Set === 'undefined') {
    window.Set = function() {
        this.items = {};
        this.size = 0;
    };

    window.Set.prototype.add = function(value) {
        if (!this.has(value)) {
            this.items[value] = value;
            this.size++;
        }
        return this;
    };

    window.Set.prototype.has = function(value) {
        return Object.prototype.hasOwnProperty.call(this.items, value);
    };

    window.Set.prototype.delete = function(value) {
        if (this.has(value)) {
            delete this.items[value];
            this.size--;
            return true;
        }
        return false;
    };

    window.Set.prototype.clear = function() {
        this.items = {};
        this.size = 0;
    };
}

// Fix for ResizeObserver
if (typeof ResizeObserver === 'undefined') {
    window.ResizeObserver = function(callback) {
        this.callback = callback;
        this.elements = [];

        // Mock implementation
        this.observe = function(element) {
            if (this.elements.indexOf(element) === -1) {
                this.elements.push(element);

                // Simulate a resize event
                var self = this;
                setTimeout(function() {
                    var entry = {
                        target: element,
                        contentRect: {
                            width: element.clientWidth || 100,
                            height: element.clientHeight || 100,
                            top: 0,
                            left: 0,
                            bottom: (element.clientHeight || 100),
                            right: (element.clientWidth || 100)
                        }
                    };
                    self.callback([entry]);
                }, 100);
            }
        };

        this.unobserve = function(element) {
            var index = this.elements.indexOf(element);
            if (index !== -1) {
                this.elements.splice(index, 1);
            }
        };

        this.disconnect = function() {
            this.elements = [];
        };
    };
}

// Fix for WeakMap if needed
if (typeof WeakMap === 'undefined') {
    window.WeakMap = function() {
        this.items = {};
    };

    window.WeakMap.prototype.set = function(key, value) {
        this.items[key] = value;
        return this;
    };

    window.WeakMap.prototype.get = function(key) {
        return this.items[key];
    };

    window.WeakMap.prototype.has = function(key) {
        return Object.prototype.hasOwnProperty.call(this.items, key);
    };

    window.WeakMap.prototype.delete = function(key) {
        if (this.has(key)) {
            delete this.items[key];
            return true;
        }
        return false;
    };
}

// Fix for checkVisibility function
Element.prototype.checkVisibility = function(options) {
    return true;
};

// Fix for includes function if needed
if (!String.prototype.includes) {
    String.prototype.includes = function(search, start) {
        'use strict';
        if (typeof start !== 'number') {
            start = 0;
        }

        if (start + search.length > this.length) {
            return false;
        } else {
            return this.indexOf(search, start) !== -1;
        }
    };
}

// Fix for autoplay property
HTMLMediaElement.prototype.autoplay = false;

console.log('Amazon Map polyfill and fixes loaded');
