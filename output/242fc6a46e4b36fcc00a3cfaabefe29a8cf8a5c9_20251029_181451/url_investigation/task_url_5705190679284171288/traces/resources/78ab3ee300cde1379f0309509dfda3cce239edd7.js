var modalShow = false;
const clearAllDropDownMenu = function (parentsDropdownMenu = []) {
  const $openDropdowns = $('.dummy-select-menu:visible').not($(this).next('.dummy-select-menu')).hide();
  if ($openDropdowns.length) {
    const $arrowIcons = $openDropdowns.prev('.dummy-select').find('.select-arrow-svg');
    $openDropdowns.hide();
    $arrowIcons.removeClass('-rotate-180');
    $openDropdowns.find('.select-tick-svg').remove();
    $openDropdowns.find('.select-menu-item').removeClass('font-600');
  }
  const $dropdownMenu = $('.dropdown-menu > div:visible');
  if ($dropdownMenu.length) {
    if (parentsDropdownMenu.length) {
      $dropdownMenu.not($dropdownMenu).removeClass('active');
    } else {
      $dropdownMenu.removeClass('active');
    }
  }
  const rowTitleDescription = $('.rowTitle_description').not($(this));
  if (rowTitleDescription.length) {
    rowTitleDescription.hide();
  }
  const tooltipDescription = $('.tooltip_description').not($(this));
  if (tooltipDescription.length) {
    tooltipDescription.hide();
  }
  $(document).off('keydown');
}
function scrollToTop() {
  $("html, body").animate({
    scrollTop: "0px"
  }, 0);
}
$(function () {
  $(document).on('click', function (event) {
    clearAllDropDownMenu();
  });
  $('.header-and-footer-2024').find('.dropdown-menu > button').click(function (event) {
    const parentsDropdownMenu = $(this).parents('.dropdown-menu').parents('.dropdown-menu');
    event.stopPropagation();
    const content = $(this).next('div');
    if (content.is(':visible')) {
      content.removeClass('active');
    } else {
      clearAllDropDownMenu(parentsDropdownMenu);
      content.addClass('active');
    }
  });

  $('.header-and-footer-2024').find('.collapsible-content > button').click(function (event) {
    event.stopPropagation();
    const content = $(this).next('div');;
    content.toggle();
    console.log(content.is(':visible'));
    if (content.is(':visible')) {
      $(this).addClass('active');
    } else {
      $(this).removeClass('active');
    }
  });

  const $headerLogo = $('.header-and-footer-2024').find('.header-logo');
  const $headerMobile = $('.header-and-footer-2024').find('.header-mobile');
  const $headerMobileBackButton = $('.header-and-footer-2024').find('.header-mobile-back-button');
  const $headerMobileTitle = $headerMobileBackButton.find('.title');
  const $headerMobileButton = $('.header-and-footer-2024').find('.header-mobile-button');
  const $headerMobileSwitch = $('.header-and-footer-2024').find('.header-mobile-switch');
  const $headerMobileMenu = $('.header-and-footer-2024').find('.header-mobile-menu');
  $headerMobileBackButton.click(function () {
    $headerLogo.show();
    $headerMobile.hide();
    $headerMobileBackButton.hide();
    $headerMobileMenu.show();
  });

  $headerMobileButton.click(function () {
    const $target = $('.' + $(this).data("target"));
    const $title = $(this).data("title");
    $headerLogo.hide();
    $headerMobile.hide();
    $headerMobileBackButton.show().css('display', 'flex');
    $headerMobileTitle.html($title);
    $target.show();
  });

  $headerMobileSwitch.click(function () {
    if ($headerMobileBackButton.is(':visible') || $headerMobileMenu.is(':visible')) {
      $headerLogo.show();
      $headerMobile.hide();
      $headerMobileBackButton.hide();
      $('html,body').css('overflow', 'visible');
      $('header').removeClass('sticky-fixed');
    } else {

      $headerMobileMenu.toggle();
      $('html,body').css('overflow', 'hidden');
      $('header').addClass('sticky-fixed');
    }
  });

  $mobileChooseLanguage = $('.header-and-footer-2024').find('.mobile-choose-language');
  $mobileChooseLanguageButton = $('.header-and-footer-2024').find('.mobile-choose-language-button');
  function handleChooseLanguageToggle() {
    if ($mobileChooseLanguage.is(':visible')) {
      $mobileChooseLanguage.hide();
      $('html,body').css('overflow', 'visible');
    } else {
      $mobileChooseLanguage.show();
      $('html,body').css('overflow', 'hidden');
    }
  }

  $mobileChooseLanguageButton.click(function () {
    handleChooseLanguageToggle();
  })

  $('header').removeClass('sticky-down');
  $('header').addClass('sticky-up');
  var prevScrollTop = 0;
  var scrollHandler = function (event) {
    var st = $(this).scrollTop();
    var direction = st < prevScrollTop ? 'up' : 'down';
    prevScrollTop = st;
    setTimeout(function () {
      if (st > $('header').height() * 2) {
        if (direction === 'up') {
          if (!$('header').hasClass('sticky-up')) {
            $('header').removeClass('sticky-down');
            $('header').addClass('sticky-up');
          }
        } else {
          if (!$('header').hasClass('sticky-down')) {
            $('header').removeClass('sticky-up');
            $('header').addClass('sticky-down');
          }
        }
      }
    }, 100);
  };
  $(window).scroll(function () {
    scrollHandler();
  });
  $(window).on('resize', function () {
    if ($(window).width() > 1024){
      $('header').removeClass('sticky-fixed');
      if(!modalShow){
        $('html,body').css('overflow','visible');
      }
    } else {
      if($headerMobileMenu.is(':visible')){
        $('html,body').css('overflow','hidden');
        $('header').addClass('sticky-fixed');
      }
    }
  });
  //sectionAnimation();
});