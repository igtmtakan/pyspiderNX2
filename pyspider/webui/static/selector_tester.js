// Selector Tester JavaScript

$(function() {
    // Initialize CodeMirror for HTML preview
    var htmlEditor = CodeMirror.fromTextArea(document.getElementById('html-content'), {
        mode: 'text/html',
        lineNumbers: true,
        theme: 'default',
        readOnly: true
    });

    // Initialize CodeMirror for JSON preview
    var jsonEditor = CodeMirror.fromTextArea(document.getElementById('json-content'), {
        mode: 'application/json',
        lineNumbers: true,
        theme: 'default',
        readOnly: true
    });

    // Initialize CodeMirror for result preview
    var resultEditor = CodeMirror.fromTextArea(document.getElementById('result-content'), {
        mode: 'application/json',
        lineNumbers: true,
        theme: 'default',
        readOnly: true
    });

    // Initialize selector type dropdown
    $('#selector-type').change(function() {
        var selectorType = $(this).val();
        
        // Show/hide appropriate input fields based on selector type
        $('.selector-input').hide();
        $('#' + selectorType + '-input').show();
        
        // Show/hide appropriate content preview based on selector type
        if (['css', 'xpath', 'css4', 'regex', 'xquery'].includes(selectorType)) {
            $('#html-preview').show();
            $('#json-preview').hide();
        } else if (['jsonpath', 'jmespath', 'graphql'].includes(selectorType)) {
            $('#html-preview').hide();
            $('#json-preview').show();
        }
        
        // Update placeholder text
        updatePlaceholder(selectorType);
    });

    // Initialize attribute input
    $('#attribute-input').hide();
    $('#use-attribute').change(function() {
        if ($(this).is(':checked')) {
            $('#attribute-input').show();
        } else {
            $('#attribute-input').hide();
        }
    });

    // Initialize transformers section
    $('#add-transformer').click(function() {
        var transformerTemplate = $('#transformer-template').html();
        $('#transformers-container').append(transformerTemplate);
        
        // Initialize the new transformer's select
        $('.transformer-select').last().change(function() {
            updateTransformerParams($(this));
        });
        
        // Initialize remove button
        $('.remove-transformer').last().click(function() {
            $(this).closest('.transformer-row').remove();
        });
    });

    // Test selector button
    $('#test-selector').click(function() {
        testSelector();
    });

    // Load URL button
    $('#load-url').click(function() {
        var url = $('#url-input').val();
        if (url) {
            loadUrl(url);
        }
    });

    // Save selector button
    $('#save-selector').click(function() {
        saveSelector();
    });

    // Load selector button
    $('#load-selector').click(function() {
        loadSelector();
    });

    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();

    // Initialize selector type change event
    $('#selector-type').trigger('change');
});

// Update placeholder text based on selector type
function updatePlaceholder(selectorType) {
    var placeholders = {
        'css': 'div.content > h1',
        'xpath': '//div[@class="content"]/h1',
        'css4': 'div.content > h1:first-of-type',
        'regex': '<h1>(.*?)</h1>',
        'jsonpath': '$.store.book[*].author',
        'jmespath': 'store.book[*].author',
        'graphql': 'query { hero { name } }',
        'xquery': 'for $x in //book return $x/title'
    };
    
    $('#selector-input').attr('placeholder', placeholders[selectorType] || '');
}

// Update transformer parameters based on transformer type
function updateTransformerParams(select) {
    var transformer = select.val();
    var paramsContainer = select.closest('.transformer-row').find('.transformer-params');
    
    // Clear existing params
    paramsContainer.empty();
    
    // Add params based on transformer type
    switch (transformer) {
        case 'replace':
            paramsContainer.append('<input type="text" class="form-control param-input" placeholder="Old string" name="param1">');
            paramsContainer.append('<input type="text" class="form-control param-input" placeholder="New string" name="param2">');
            break;
        case 'regex_replace':
            paramsContainer.append('<input type="text" class="form-control param-input" placeholder="Pattern" name="param1">');
            paramsContainer.append('<input type="text" class="form-control param-input" placeholder="Replacement" name="param2">');
            break;
        case 'regex_extract':
            paramsContainer.append('<input type="text" class="form-control param-input" placeholder="Pattern" name="param1">');
            paramsContainer.append('<input type="number" class="form-control param-input" placeholder="Group (default: 0)" name="param2" value="0">');
            break;
        case 'slice':
            paramsContainer.append('<input type="number" class="form-control param-input" placeholder="Start index" name="param1" value="0">');
            paramsContainer.append('<input type="number" class="form-control param-input" placeholder="End index (optional)" name="param2">');
            break;
        case 'join':
            paramsContainer.append('<input type="text" class="form-control param-input" placeholder="Separator (default: space)" name="param1" value=" ">');
            break;
        case 'split':
            paramsContainer.append('<input type="text" class="form-control param-input" placeholder="Separator (default: space)" name="param1" value=" ">');
            break;
        case 'nth':
            paramsContainer.append('<input type="number" class="form-control param-input" placeholder="Index" name="param1" value="0">');
            break;
        case 'default':
        case 'if_none':
        case 'if_empty':
            paramsContainer.append('<input type="text" class="form-control param-input" placeholder="Default value" name="param1">');
            break;
        case 'format_date':
        case 'format_datetime':
        case 'date_to_string':
            paramsContainer.append('<input type="text" class="form-control param-input" placeholder="Format (e.g. %Y-%m-%d)" name="param1">');
            break;
    }
}

// Test selector
function testSelector() {
    var selectorType = $('#selector-type').val();
    var selector = $('#selector-input').val();
    var attribute = $('#use-attribute').is(':checked') ? $('#attribute-input').val() : null;
    var url = $('#url-input').val();
    
    // Get transformers
    var transformers = [];
    $('.transformer-row').each(function() {
        var name = $(this).find('.transformer-select').val();
        var params = {};
        
        $(this).find('.param-input').each(function(index) {
            var paramName = $(this).attr('name');
            var paramValue = $(this).val();
            params[paramName] = paramValue;
        });
        
        transformers.push({
            name: name,
            params: params
        });
    });
    
    // Show loading indicator
    $('#result-container').html('<div class="text-center"><i class="fa fa-spinner fa-spin"></i> Testing selector...</div>');
    
    // Send request to server
    $.ajax({
        url: '/api/test_selector',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            selector_type: selectorType,
            selector: selector,
            attribute: attribute,
            url: url,
            transformers: transformers
        }),
        success: function(response) {
            // Update result
            resultEditor.setValue(JSON.stringify(response.result, null, 2));
            
            // Update content preview
            if (response.content_type === 'html') {
                htmlEditor.setValue(response.content);
                $('#html-preview').show();
                $('#json-preview').hide();
            } else if (response.content_type === 'json') {
                jsonEditor.setValue(JSON.stringify(response.content, null, 2));
                $('#html-preview').hide();
                $('#json-preview').show();
            }
            
            // Show error if any
            if (response.error) {
                $('#error-container').html('<div class="alert alert-danger">' + response.error + '</div>');
                
                // Show suggestions if any
                if (response.suggestions && response.suggestions.length > 0) {
                    var suggestionsHtml = '<div class="alert alert-info"><strong>Suggestions:</strong><ul>';
                    response.suggestions.forEach(function(suggestion) {
                        suggestionsHtml += '<li>' + suggestion + '</li>';
                    });
                    suggestionsHtml += '</ul></div>';
                    $('#error-container').append(suggestionsHtml);
                }
                
                // Show auto-fixed selector if available
                if (response.fixed_selector) {
                    var fixedHtml = '<div class="alert alert-success"><strong>Auto-fixed selector:</strong> ' + 
                        response.fixed_selector + ' <button class="btn btn-sm btn-primary use-fixed-selector">Use This</button></div>';
                    $('#error-container').append(fixedHtml);
                    
                    // Use fixed selector button
                    $('.use-fixed-selector').click(function() {
                        $('#selector-input').val(response.fixed_selector);
                        if (response.fixed_selector_type && response.fixed_selector_type !== selectorType) {
                            $('#selector-type').val(response.fixed_selector_type).trigger('change');
                        }
                    });
                }
            } else {
                $('#error-container').empty();
            }
            
            // Highlight matched elements in HTML preview
            if (response.matched_elements && response.content_type === 'html') {
                highlightMatchedElements(response.matched_elements);
            }
        },
        error: function(xhr, status, error) {
            $('#result-container').html('<div class="alert alert-danger">Error: ' + error + '</div>');
        }
    });
}

// Load URL
function loadUrl(url) {
    // Show loading indicator
    $('#result-container').html('<div class="text-center"><i class="fa fa-spinner fa-spin"></i> Loading URL...</div>');
    
    // Send request to server
    $.ajax({
        url: '/api/load_url',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            url: url
        }),
        success: function(response) {
            // Update content preview
            if (response.content_type === 'html') {
                htmlEditor.setValue(response.content);
                $('#html-preview').show();
                $('#json-preview').hide();
            } else if (response.content_type === 'json') {
                jsonEditor.setValue(JSON.stringify(response.content, null, 2));
                $('#html-preview').hide();
                $('#json-preview').show();
            }
            
            // Clear result
            resultEditor.setValue('');
            
            // Show error if any
            if (response.error) {
                $('#error-container').html('<div class="alert alert-danger">' + response.error + '</div>');
            } else {
                $('#error-container').empty();
            }
        },
        error: function(xhr, status, error) {
            $('#result-container').html('<div class="alert alert-danger">Error: ' + error + '</div>');
        }
    });
}

// Save selector
function saveSelector() {
    var name = prompt('Enter a name for this selector:');
    if (!name) return;
    
    var selectorType = $('#selector-type').val();
    var selector = $('#selector-input').val();
    var attribute = $('#use-attribute').is(':checked') ? $('#attribute-input').val() : null;
    
    // Get transformers
    var transformers = [];
    $('.transformer-row').each(function() {
        var name = $(this).find('.transformer-select').val();
        var params = {};
        
        $(this).find('.param-input').each(function(index) {
            var paramName = $(this).attr('name');
            var paramValue = $(this).val();
            params[paramName] = paramValue;
        });
        
        transformers.push({
            name: name,
            params: params
        });
    });
    
    // Save to localStorage
    var savedSelectors = JSON.parse(localStorage.getItem('savedSelectors') || '{}');
    savedSelectors[name] = {
        selector_type: selectorType,
        selector: selector,
        attribute: attribute,
        transformers: transformers
    };
    localStorage.setItem('savedSelectors', JSON.stringify(savedSelectors));
    
    alert('Selector saved successfully!');
}

// Load selector
function loadSelector() {
    var savedSelectors = JSON.parse(localStorage.getItem('savedSelectors') || '{}');
    var names = Object.keys(savedSelectors);
    
    if (names.length === 0) {
        alert('No saved selectors found.');
        return;
    }
    
    var name = prompt('Enter the name of the selector to load:\n\nAvailable selectors: ' + names.join(', '));
    if (!name || !savedSelectors[name]) {
        alert('Selector not found.');
        return;
    }
    
    var selectorData = savedSelectors[name];
    
    // Set selector type
    $('#selector-type').val(selectorData.selector_type).trigger('change');
    
    // Set selector
    $('#selector-input').val(selectorData.selector);
    
    // Set attribute
    if (selectorData.attribute) {
        $('#use-attribute').prop('checked', true).trigger('change');
        $('#attribute-input').val(selectorData.attribute);
    } else {
        $('#use-attribute').prop('checked', false).trigger('change');
    }
    
    // Set transformers
    $('#transformers-container').empty();
    if (selectorData.transformers && selectorData.transformers.length > 0) {
        selectorData.transformers.forEach(function(transformer) {
            $('#add-transformer').click();
            var row = $('.transformer-row').last();
            row.find('.transformer-select').val(transformer.name).trigger('change');
            
            // Set params
            if (transformer.params) {
                Object.keys(transformer.params).forEach(function(paramName, index) {
                    row.find('.param-input[name="' + paramName + '"]').val(transformer.params[paramName]);
                });
            }
        });
    }
    
    alert('Selector loaded successfully!');
}

// Highlight matched elements in HTML preview
function highlightMatchedElements(elements) {
    // TODO: Implement highlighting of matched elements in the HTML preview
    console.log('Matched elements:', elements);
}
