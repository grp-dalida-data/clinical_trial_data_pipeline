function searchToggle(obj, evt) {
    var container = $(obj).closest('.search-wrapper');

    if (!container.hasClass('active')) {
        container.addClass('active');
        evt.preventDefault();
    } else if (container.hasClass('active') && $(obj).closest('.input-holder').length == 0) {
        container.removeClass('active');
        // clear input
        container.find('.search-input').val('');
    }
}

// Ensure the form is submitting properly
$(document).ready(function() {
    $(".search-form").on('submit', function(evt) {
        var container = $(this).closest('.search-wrapper');
        if (container.hasClass('active')) {
            return true;
        } else {
            // Prevent form submission
            evt.preventDefault();
        }
    });
});
