$(document).ready(() => {
  let dropDown = $(".tm-sidebar-drop");
  let caret = $(".tm-sidebar-caret");

  $(dropDown).each((ind, val) => {
    $(val).click(() => {
      $(caret.not(caret[ind])).removeClass("ion-ios-arrow-down");
      $(caret.not(caret[ind])).addClass("ion-ios-arrow-back");
      $(caret[ind]).toggleClass("ion-ios-arrow-down");
      $(caret[ind]).toggleClass('ion-ios-arrow-back');
    });
  });

  $('#modelId').on('show.bs.modal', event => {
    var button = $(event.relatedTarget);
    var modal = $(this);
    // console.log(modal);
    // Use above variables to manipulate the DOM

  });

  // $('.alert').alert();

    let sidebar = $('.tm-sidebar');
    let content = $('.tm-content');

  $('#tm-semi-close-nav').click((e) => {
    $(sidebar).toggleClass('tm-w-0');
    $(content).toggleClass('tm-ml-0');
    $('#tm-semi-close-nav').children('i.icon').toggleClass('ion-md-menu');
  })
});