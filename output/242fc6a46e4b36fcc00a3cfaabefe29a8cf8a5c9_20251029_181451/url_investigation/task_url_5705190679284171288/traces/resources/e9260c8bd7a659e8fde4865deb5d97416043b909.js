/**
 * Author: Jacky
 * base on tip-modal.html
 * ex: <include file="public@tools/tip-modal"/>
 */

var countDownTimeLimit = 60;
let foxitTip = {
    // usage: foxitTip.alert({title: 'success', content: 'Thank you!', onClose: function(){alert(111)}});
    alert: function (params, isModal) {
        isModal = isModal || false;
        let defaultParams = {
            modalID: 'foxit_alert',
            title: '',
            content: '',
            onClose: '',
            onCloseData: {},
            onInit: '',
            onInitData: {}
        };
        $.extend(defaultParams, params);

        let modalSlt = $("#" + defaultParams.modalID);
        modalSlt.find('.modal-title').html(defaultParams.title);
        modalSlt.find('.modal-body').html(defaultParams.content);
        
        if(typeof params.onClose === 'string') {
            modalSlt.find('button.fx-modal-close.btn-alert').html(defaultParams.onClose);
        }

        if (isModal) {
            modalSlt.modal({backdrop: "static"});
        } else {
            modalSlt.removeClass('modal-visible');
            modalSlt.addClass('modal-visible');
        }

        if (typeof defaultParams.onClose === 'function') {
            modalSlt.find('button.fx-modal-close').off('click').on('click',function () {
                defaultParams.onClose(defaultParams.onCloseData);
            });
        }

        if (typeof defaultParams.onInit === 'function') {
            defaultParams.onInit();
        }
    },
    alert_activate_myapps: function (params, isModal) {
        isModal = isModal || false;
        let defaultParams = {
            modalID: 'foxit_alert',
            title: '',
            content: '',
            onClose: '',
            onCloseData: {},
            onInit: '',
            onInitData: {},
            btnClose: '',
        };
        $.extend(defaultParams, params);

        let modalSlt = $("#" + defaultParams.modalID);
        modalSlt.find('.modal-title').html(defaultParams.title);
        modalSlt.find('.modal-body').html(defaultParams.content);

        if (!dataFilter.isEmpty(defaultParams.btnClose)) {
            modalSlt.find('button.btn-alert').html(defaultParams.btnClose);
        }
        if (isModal) {
            modalSlt.modal({backdrop: "static"});
        } else {
            modalSlt.removeClass('modal-visible');
            modalSlt.addClass('modal-visible');
        }

        if (typeof defaultParams.onClose === 'function') {
            modalSlt.find('button.fx-modal-close').off('click').on('click',function () {
                defaultParams.onClose(defaultParams.onCloseData);
            });
        }

        if (typeof defaultParams.onInit === 'function') {
            defaultParams.onInit();
        }
    },
    loading: function (type, tip) {
        tip = tip === 'undefined' ? '' : tip;
        let slt = $("#foxit_loading");
        if (type === 'show') {
            foxitTip.cleanModal();

            //slt.modal({backdrop: "static"});
            slt.removeClass('modal-visible');
            slt.addClass('modal-visible');
            slt.find('.tip').html(tip);
        } else if (type === 'progressbar') {
            foxitTip.cleanModal();
            slt.removeClass('modal-visible');
            slt.addClass('modal-visible');
            slt.find('.tip').html('loading...');
            slt.find('.tip').attr('id','progressbar');
        } else {
            //slt.modal('hide');
            slt.removeClass('modal-visible');
            slt.find('.tip').html('');

            foxitTip.cleanModal();
        }
    },
    cleanModal: function () {
        let slt = $('.modal-backdrop.fade.in');
        let length = slt.length;

        for (let i = 0; i < length; i++) {
            $(slt[i]).remove();
        }
    },
    // usage: foxitTip.confirm({title: 'success', content: 'Thank you!', onClose: function(){alert(111)}, onOk: function(){alert(222)}});
    confirm: function (params) {
        let defaultParams = {
            title: '',
            content: '',
            onOk: '',
            onClose: '',
            onCloseData: {},
            onOkData: {},
            onInit: '',
            onInitData: {},
            btnOk: '',
            btnClose: '',
            code: '',
        };
        $.extend(defaultParams, params);
        let modalSlt = $("#foxit_confirm");
        modalSlt.find('.modal-title').html(defaultParams.title);
        modalSlt.find('.modal-body').html(defaultParams.content);

        // modalSlt.modal({backdrop: "static"});
        modalSlt.removeClass('modal-visible');
        modalSlt.addClass('modal-visible');
        if (defaultParams.code == '100000') {
            modalSlt.find('button.btn-ok').attr('id', 'upgrade-now');
        }
        if (!dataFilter.isEmpty(defaultParams.btnOk)) {
            modalSlt.find('button.btn-ok').html(defaultParams.btnOk);
            if (!dataFilter.isEmpty(defaultParams.btnOkColor)) {
                modalSlt.find('button.btn-ok').css('background-color', defaultParams.btnOkColor);

            }
        }
        if (!dataFilter.isEmpty(defaultParams.btnClose)) {
            modalSlt.find('button.btn-close').html(defaultParams.btnClose);
        }

        if (typeof defaultParams.onOk === 'function') {
            modalSlt.find('button.btn-ok').off('click').on('click',function () {
                // modalSlt.modal('hide');
                modalSlt.removeClass('modal-visible');
                defaultParams.onOk(defaultParams.onOkData);
            });
        }

        if (typeof defaultParams.onClose === 'function') {
            modalSlt.find('button.close,button.btn-close').off('click').on('click',function () {
                defaultParams.onClose(defaultParams.onCloseData);
            });
        }

        if (typeof defaultParams.onInit === 'function') {
            defaultParams.onInit();
        }
    },
    /**
     * popover
     * @param params
     * @usage
     foxitTip.popover({
        title: 'you can customize this popover',
        content: 'Here is content area',
        onClose: function(){alert(111)},
        onCloseData: {},
        // will display in btn area
        btnList: [
            {uniqueId: 'buttonOne', text: 'try it', params: 'nice body!', doClick: function(c){alert(c)}},
            {uniqueId: 'buttonTwo', text: 'try again', doClick: function(){alert('hi!')}}
        ],
        onInit: '',
        onInitData: {},
        btnStyle: '<style>#foxit_popover .modal-footer{text-align:center;} .buttonOne{margin-right: 80px}</style>',
    });
     */
    popoverClose: () => {
        $("#foxit_popover").removeClass('modal-visible');
    },
    alertClosePooling: () => {
        $("#foxit_alert_pooling").removeClass('in');
        $("#foxit_alert_pooling").css("display", "");
    },
    popover: function (params) {
        let defaultParams = {
            title: '',
            content: '',
            onClose: '',
            onCloseData: {},
            btnList: [],
            onInit: '',
            onInitData: {},
            btnStyle: ''
        };
        $.extend(defaultParams, params);

        let modalSlt = $("#foxit_popover");
        modalSlt.find('.modal-title').html(defaultParams.title);
        modalSlt.find('.modal-body').html(defaultParams.content);

        let btnListHtml = '';
        if (!dataFilter.isEmpty(params.btnList)) {
            Object.keys(params.btnList).forEach(function (k) {
                btnListHtml += '<button type="button" class="btn btn-default ' + params.btnList[k].uniqueId + '" data-dismiss="modal">' + params.btnList[k].text + '</button>';
            });
        }
        btnListHtml += defaultParams.btnStyle;
        modalSlt.find('.modal-footer').html(btnListHtml);

        if (!dataFilter.isEmpty(params.btnList)) {
            Object.keys(params.btnList).forEach(function (k) {
                if (typeof params.btnList[k].doClick === 'function') {
                    modalSlt.find('button.' + params.btnList[k].uniqueId).off('click').on('click',function () {
                        params.btnList[k].doClick(params.btnList[k].params);
                    });
                }
            });
        }

        // modalSlt.modal({backdrop: "static"});
        modalSlt.removeClass('modal-visible');
        modalSlt.addClass('modal-visible');

        if (typeof defaultParams.onClose === 'function') {
            modalSlt.find('button.close,button.btn-close').off('click').on('click',function () {
                defaultParams.onClose(defaultParams.onCloseData);
            });
        }

        if (typeof defaultParams.onInit === 'function') {
            defaultParams.onInit();
        }
    },
    // 倒计时
    countDownTime: function (slt) {
        if (countDownTimeLimit === 0) {
            slt.attr('disabled', false);
            if (typeof foxitJsLang === 'object') {
                slt.html(foxitJsLang.get_your_verification_code);
            } else {
                slt.html(foxitJsLang.get_your_verification_code);
            }
            countDownTimeLimit = 60;
        } else {
            slt.attr('disabled', true);
            if (typeof foxitJsLang === 'object') {
                slt.html(foxitJsLang.resend + '(' + countDownTimeLimit + ')');
            } else {
                slt.html('Resend(' + countDownTimeLimit + ')');
            }
            countDownTimeLimit--;
            setTimeout(function () {
                foxitTip.countDownTime(slt);
            }, 1000)
        }
    },
    pop: function (id) {
        let modalSlt = $("#" + id);
        // modalSlt.modal({backdrop: "static"});
        modalSlt.removeClass('modal-visible');
        modalSlt.addClass('modal-visible');
    },
    transparent: function (type) {
        let slt = $('#fx-shade');
        if (type === 'show') {
            slt.css('display', 'block');
        } else {
            slt.css('display', 'none');
        }
    },
    // 初始化
    init: function () {
        $(document).on('click', '.fx-modal-close', function () {
            //$(this).parents('div.modal').modal('hide');
            $(this).parents('div.modal').removeClass('modal-visible');
        })
    },
};
jQuery(document).ready(function () {
    $('.modal .modal-body')
        .css('max-height', window.screen.availHeight * 0.55 + 'px')
        .css('overflow', 'auto');

    foxitTip.init();
});
