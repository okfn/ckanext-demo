(function (jQuery) {
  jQuery('.close').click(function (event) {
    event.preventDefault();
    jQuery(this).parent().removeClass('fade-in');
  });

  jQuery(window).on('load', function () {
    jQuery('.module-info-overlay').each(function () {
      var panel = jQuery(this);
      setTimeout(function () {
        panel.addClass('fade-in');
      }, 1500);
    });
  });
})(this.jQuery);
