/**
 * Author Jacky
 * 这边是公用的
 */

let foxitJsLang = {
    // 公共部分
    'confirm': 'OK',
    'cancel': 'Annuler',
    'delete': 'Supprimer',
    'select': 'Sélectionner',
    'operation_confirm': 'Confirmer',
    'please_select': 'Sélectionnez',
    'captcha_is_need': 'Please input the picture contains 6 characters.',
    'business_error': 'Error',
    'unknown_business_deal_type': 'Unknown business type, please contact administrator.',
    'approximately': 'appr.',
    'get_your_verification_code': 'Obtenir le code de vérification',
    'resend': 'Renvoyer',
    'tip_for_offline': 'La session a expiré, reconnectez-vous.',
    'please_retry': 'Please retry',
    'loading': 'chargement',
    'network_error_please_try_again': 'Erreur réseau, essayez à nouveau!',
    'please_complete_the_human_verification_first': 'Veuillez cocher la case "Je ne suis pas un robot" pour continuer.',
    'state': 'State',
    'please_input_a_correct_email_address': 'Veuillez saisir une adresse e-mail valide.',
    'optional': 'Facultatif',

    // modal
    'error': 'Fehler',
    'success': 'Success',
    'complete': 'Complet',
    'second_confirm': 'Vous y êtes presque !',
    'hello': 'Hello',
    'attention': 'Remarque',
    'note': 'Remarque',
    'yes': 'Yes',
    'continue': 'Continuer',
    'message': 'Message',

    // 信用卡
    'cardholders_name': 'Détenteur de la carte',
    'cardholders_placeholder': 'Détenteur de la carte',
    'cardholders_placeholder_paypal': 'Détenteur de la carte',
    'card_number': 'Numéro de carte bancaire',
    'card_number_placeholder': 'Chiffres uniquement, sans espaces ni tirets.',
    'card_expiry': 'Date d\'expiration',
    'card_cvc': 'Cryptogramme visuel',
    'redirect_to_banking_site': 'Vous allez être redirigé vers le site bancaire pour terminer votre paiement.',
    'redirect_to_banking_site_paypal': 'After submitting your order, you will receive PayPal Instructions to continue your payment. Once your payment has been successfully completed and confirmed by PayPal, delivery of the ordered products will be completed.',
    'cardholders_name_is_required': 'Cardholders name is required',
    'card_number_is_required': 'Card\'s No. is required',
    'card_cvc_is_required': 'Card\'s CVC code is required',
    'card_expm_is_required': 'Card\'s Expired Month is required',
    'card_expy_is_required': 'Card\'s Expired Year is required',

    // validate
    'very_weak': 'Très faible',
    'weak': 'Faible',
    'mediocre': 'Médiocre',
    'strong': 'Fort',
    'very_strong': 'Très fort',

    // 月份
    'Jan': 'Janv.',
    'Feb': 'Févr.',
    'Mar': 'Mars',
    'Apr': 'Avr.',
    'May': 'Mai',
    'Jun': 'Juin',
    'Jul': 'Juil.',
    'Aug': 'Août',
    'Sep': 'Sept.',
    'Oct': 'Oct.',
    'Nov': 'Nov.',
    'Dec': 'Déc.',

    // foxit esign euro purchase tip
    'esign_euro_purchase_tip': 'Please login to your Foxit eSign service and purchase the plan of your choice from within the application. If you do not have an account, please go <a href="https://www.esigngenie.com/registration/" target="_blank" rel="nofollow">here</a>.',

    // 业务部分
    mall: {
        'license_quantity': 'Nombre de licences',
        'site_license': 'Site License',
        'envelopes': '# Enveloppes',
        'remove_cart_item_confirm': 'Voulez-vous vraiment supprimer cet élément de votre panier?',
        'discount_information': 'Discount Coupon Information',
        'price_not_found': 'Le prix du produit actuel est introuvable. ',
        'please_select_extra': 'Extra is required.',
        'show_details': 'Cliquez pour en savoir plus',
        'hide_details': '',
        'from': 'from',
        'exempt': 'Exempter',
        'paying': 'Paiement',
        'init_menu_language_error': 'Une erreur s\'est produite lors de l\'initialisation de la langue du menu.',
        'tax_tip_calculated_desc': 'Remarque : nous avons calculé les taxes et les avons ajoutées à votre commande. Si vous pensez que vous devez être exempté de taxes, contactez-nous au numéro +49 30 394050-0 pour une commande hors-ligne.',
        'tax_tip_no_need_desc': 'Vous ne devez payer aucune taxe.',
        'one_time': '1 fois',
        'annually': 'Annuel',
        'monthly': 'Mensuel',
        'subscription': 'Abonnement annuel',
        'subscription-monthly': 'Formule mensuelle',
        'subscription-monthly_': 'Abonnement mensuel',
        'annually_y': 'Formule annuelle',
        'annually_prepaid': 'Formule annuelle, prépayé',
        'monthly_y': 'par licence/an',
        'per_license_per_year': 'par licence/an',
        'subtotal': 'Sous-total',
        'total_amount': 'Montant total',
        'tax': 'Taxes',
        'credit_card': 'Carte bancaire',
        'new_credit_card': 'Nouvelle carte bancaire',
        'per_license': 'Par Licence',
        'no_i_want_to_use_another_account': 'No, I want to use another account',
        'retry': 'Réessayer',
        'proceed_without_tax_number': 'POURSUIVRE SANS NUMÉRO DE TAXE',
        'subscription_yearly_prepaid_year': '/an',
        'subscription_monthly_year_month': '/mois',

        // 支付方式
        'please_select_payment_method': 'Sélectionnez un moyen de paiement.',
        'please_input_cardholders_name': 'Please Input Cardholder\'s Name',
        'network_error_use_another_payment_instead': 'Le mode de paiement que vous avez sélectionné n\'est malheureusement pas disponible en raison de problèmes réseau. Réessayez ultérieurement ou choisissez un autre mode de paiement.',

        // upgrade
        'FPMRK_do_not_support_upgrade': 'Entrez la clé d\'enregistrement, car ce numéro de série n\'est pas applicable pour la mise à niveau. ',
        'the_verification_code_has_been_sent_successfully_please_check_your_email': 'Le code de vérification a été envoyé avec succès, veuillez vérifier votre boîte mail.',
        'the_email_verification_code_failed_to_be_sent_please_try_again_later': 'L&#39;envoi du code de vérification par e-mail a échoué, veuillez réessayer ultérieurement.',

        'month_per_user': '/ mois par utilisateur',
        'billed_annually': 'facturés annuellement',

        'see_all_features': 'Voir toutes les fonctionnalités',
        'collapse_all': 'Réduire tout',

        'items': 'Articles',
        'item': 'Article',

        'city': 'Ville',
        'address': 'Adresse',
        'optional': 'Facultatif',
        'this_feature_is_only_available_for_the_annual_prepaid_plan': 'La fonction de gestion des licences n\'est disponible que pour le plan "Annuel, prépayé".',
    },
    // 根据参数进行描述 不同语言的语法表述顺序不同
    funcDesc: {
        mall: {
            // tips for activity changing country
            activityTips: function (activityGoods) {
                let len = activityGoods.length;
                let desc = 'Ce prix n’est pas disponible dans votre région.<br/>Le prix pour votre région est de';
                Object.keys(activityGoods).forEach(function (k) {
                    if (parseInt(k) === len - 1) {
                        desc += ' ' + activityGoods[k].originPrice + ' par licence pour ' + activityGoods[k].goodsName + '.';
                    } else {
                        desc += ' ' + activityGoods[k].originPrice + ' par licence pour ' + activityGoods[k].goodsName + ',';
                    }
                });

                return desc;
            },
            // 订单详情价格标注
            orderDetailPriceTips: function (orderInfo, currencyInfo) {
                let dataContent = '<ul class="list-unstyled" style="width:200px;">';
                if (orderInfo.detail_amount_discount != 0) {
                    dataContent += '<li>Montant total à payer: ' + orderInfo.detail_amount_pay + '</li>';
                    dataContent += '<li>Montant de la remise: ' + orderInfo.detail_amount_discount + '</li>';
                    dataContent += '<li>Prix de départ total: ' + orderInfo.detail_amount_total + '</li>';
                    dataContent += '</ul>';
                } else {
                    dataContent += '<li>Prix unitaire d\'origine: ' + currencyInfo.currency_symbol + orderInfo.detail_per_price_original + '</li>';
                    dataContent += '</ul>';
                }

                return dataContent;
            },
            // 查找registration key 或 SN
            // type: phantom ifilter
            findKeyOrSn: function (productName, type) {
                let cateName = 'PhantomPDF';
                let content = '';
                switch (type) {
                    case 'phantom':
                        content += '<ol style="padding-left:25px;width:300px;">' +
                            '<li>Pour trouver votre clé d\'enregistrement&nbsp;:<br>Exécutez ' + productName + '&gt; Sélectionnez le menu «&nbsp;Aide&nbsp;»&nbsp;&gt; ' +
                            'Cliquez sur «&nbsp;Activation&nbsp;», puis sur «&nbsp;Activer ' + cateName + '&nbsp;». La clé d\'enregistrement s\'affiche, ' +
                            'au format xxxxx-xxxxx-xxxxx-xxxxx-xxxxx-xxxxx </li>' +
                            '<li>Pour trouver votre numéro de série&nbsp;:<br>Exécutez ' + productName + '&gt; Sélectionnez le menu «&nbsp;Aide&nbsp;»&nbsp;&gt; Cliquez ' +
                            'sur «&nbsp;À propos de Foxit ' + cateName + '». Le numéro de série s\'affiche.</li></ol>';
                        break;
                    case 'ifilter':
                        content += '<ol style="padding-left:25px;width:300px;">';
                        content += '<li>To locate your Serial Number:<br>Please run ' + productName + '&gt; Choose "Help" menu &gt; ';
                        content += 'Click "About ' + productName + '", you will find the SN located.</li></ol>';
                        content += '<ol style="padding-left:25px;width:300px;">' +
                            '<li>Pour trouver votre numéro de série&nbsp;:<br>Exécutez ' + productName + '&gt; Sélectionnez le menu «&nbsp;Aide&nbsp;»&nbsp;&gt; ' +
                            'Cliquez sur «&nbsp;À propos de ' + productName + '». Le numéro de série s\'affiche.</li></ol>';
                        break;
                }

                return content;
            },
            // 支付方式名称
            paymentName: function (name) {
                switch (name) {
                    case 'cards':
                        return 'Carte bancaire';
                    case 'ideal':
                        return 'iDEAL';
                    case 'giropay':
                        return 'Giropay';
                    case 'bancontact':
                        return 'Bancontact';
                    case 'sofort':
                        return 'Sofort';
                    case 'paypal_payflow_pro':
                        return 'Carte bancaire';
                    default:
                        return name;
                }
            },
            // tax tips
            taxTips: function (regionCode) {
                const regionNamesInEnglish = new Intl.DisplayNames(['en'], { type: 'region' });

                // I acknowledge that I am a registered business entity/individual for VAT in Spain.
                let VATAcknowledgeList = [
                    'AT', 'BE', 'BG', 'CY', 'HR', 'CZ', 'DK', 'EE', 'FI', 'FR',
                    'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL',
                    'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE', 'GB',
                    'TW', 'TH', 'VN'
                ];

                let GSTAcknowledgeList = [
                    'AU', 'IN', 'SG'
                ];

                let digitalGoodsAndServicesAcknowledgeList = [
                    'ID', 'MY'
                ];

                if(dataFilter.array.inArray(regionCode, VATAcknowledgeList)){
                    return 'I acknowledge that I am a registered business entity/individual for VAT in ' + regionNamesInEnglish.of(regionCode) + '.';
                }else if(dataFilter.array.inArray(regionCode, GSTAcknowledgeList)){
                    return 'I acknowledge that I am a registered business entity/individual for GST in ' + regionNamesInEnglish.of(regionCode) + '.';
                }else if(dataFilter.array.inArray(regionCode, digitalGoodsAndServicesAcknowledgeList)){
                    return 'All digital goods and services sold by Foxit to customers in ' + regionNamesInEnglish.of(regionCode) + ' are taxable.';
                }else{
                    return '';
                }
            },
            couponApplyMaxBuyNumTips: function (buyNum) {
                return 'Ce code promotionnel est valide uniquement pour les ' + buyNum + ' premières licences.';
            },
        }
    },
    wordsV: {
        'get_early_access_pricing_starting': 'Obtenez un accès anticipé aux tarifs, à partir de <b class="text-orange-550">{:priceLocalization}{:perPeriod}</b>, en ajoutant AI Assistant. Si vous n&#39;êtes pas déjà abonné, achetez un abonnement ou téléchargez Foxit PDF Reader pour commencer. Une fois acheté, AI Assistant peut être utilisé sur toutes les plateformes Foxit, y compris Foxit PDF Editor Cloud, iOS, Android, Mac, Windows et Reader.',
    },

    formCheck: {
        requiredEmail: 'Veuillez entrer une adresse e-mail valide.',
        notEmail: 'Veuillez entrer une adresse e-mail valide.',
        requiredSelect: 'Sélectionner',
        js_error_occurred: 'Les erreurs suivantes se sont produites :',
        gdpr_confirm_content: "Pour continuer, cliquez sur \"Accepter et continuer\" pour accepter les<a href=\"/product/terms-of-service.html\"> conditions d'utilisation</a> et reconnaître la<a href=\"/fr/company/privacy-policy.html\"> politique de confidentialité</a>.",
        gdpr_confirm_ok: 'Accepter et continuer',
        gdpr_confirm_close: 'Refuser',
        ac_confirm: 'Désolé, votre e-mail ne peut pas accéder à l\'essai de la gestion des licences car votre entreprise dispose déjà d\'une Admin Console existante pour gérer les licences.<br>Veuillez contacter votre administrateur d\'entreprise ou cliquez sur "Continuer" pour essayer Foxit PDF Editor+ sans gestion des licences.',
    },

    passport: {
        'find_password_send_success_message': 'Un e-mail a été envoyé dans votre boîte de réception. ' +
            'Il contient un lien sur lequel vous devez cliquer pour réinitialiser votre mot de passe. ' +
            'Pour vous assurer que vous recevrez cet e-mail dans votre boîte de réception, ' +
            'vous devez ajouter à la liste blanche l’adresse d’expédition de l’e-mail suivante : no-reply@email.foxitsoftware.com. Si vous ne recevez pas l’e-mail dans les dix minutes, ' +
            'n’hésitez pas à nous contacter à l’adresse support@' + foxitApp.EMAIL_DOMAIN + '.',
        'reset_password_success': 'Réinitialisation du mot de passe réussie.'
    },
    // 密码输入强度
    password: {
        'enter_password': 'Please Enter Password',
        'too_weak': 'Très faible',
        'weak': 'Faible',
        'should_stronger': 'Fort',
        'strong_password': 'Très fort',
        'has_illegal_characters': 'Le mot de passe contient des caractères interdits.',
    },
    member: {
        'order_details': 'Order Details',
        'query_result': 'Query Result',
        'deactivated': 'Désactivé',
        'notes': 'Remarque ',
        'cancel_subscription_notice_one': '1.En annulant le renouvellement automatique, votre abonnement expire à la prochaine date de paiement.',
        'cancel_subscription_notice_two': '2.Désactiver le renouvellement automatique de cet abonnement désactivera également le renouvellement automatique pour le Smart Redact Server.',
        'cancel_subscription_notice_two_con': '2.Désactiver le renouvellement automatique de cet abonnement désactivez également le renouvellement automatique pour Foxit Connectors.',
        'cancel_subscription_notice_two_all': '2.Désactiver le renouvellement automatique de cet abonnement désactivera également le renouvellement automatique pour Foxit Connectors et le Smart Redact Server.',
        'cancel_subscription_notice_three': 'Voulez-vous vraiment annuler ?',
        'are_you_sure_want_to_deactivate_it': 'Voulez-vous vraiment désactiver cet élément ?',
        'are_you_sure_want_to_cancel_subscription': 'En annulant votre abonnement, celui-ci expirera à la prochaine date de paiement. Voulez-vous vraiment annuler votre abonnement ?',
        'are_you_sure_want_to_renew_subscription': 'Voulez-vous vraiment renouveler automatiquement votre abonnement ?',
        'order_list_search_tip': 'N° de commande/Courrier/Produit/ID de paiement/N° de facture/N° de référence',
        'rkc_list_search_tip': 'Registration Key Code/Order#',
        'gen_rkc_list_search_tip': 'No./Product',
        'activation_log_comment_is_empty': 'Activation log comment can not be empty',
        'subscription_details': 'Détail de l\'abonnement',
        'are_you_sure_want_to_resend_invited_email': 'Voulez-vous vraiment renvoyer l\'e-mail d\'invitation ?',
        'are_you_sure_want_to_remove_member': 'Voulez-vous vraiment supprimer ce membre ?',
        'yes': 'Oui',
        'no': 'Non',
        'invalid_email': 'Certaines adresses e-mail ne sont pas valides:',
        'enter_email_address': 'S\'il vous plaît entrer votre adresse mail.',
        'add_member_over_limit': 'Le nombre de membres que vous avez ajoutés dépasse la valeur maximale.',
        'download_invoice': 'Download Invoice',
        'repeat_email': 'Trois adresses e-mail sont répétées. Supprimez-les.',
        'cancel_subscription': 'Désactiver le renouvellement automatique',
        'renew_subscription': 'L\'abonnement a été renouvelé.',
        'subscription_expires_at': 'L\'abonnement expire le ',
        'next_payment_date': 'Date du prochain paiement',
        'resume_payment': 'Activer le renouvellement automatique',
        'purchase_additional_subscription': '<span class="font-extrabold font-italic">Acheter</span> un abonnement supplémentaire',
        'purchase_additional_subscription_srs': '<span class="font-extrabold font-italic">Acheter</span> un espace de stockage supplémentaire',
        'purchase_additional_subscription_con': '<span class="font-extrabold font-italic">Acheter</span> Foxit Connectors',
        'are_you_sure_want_to_place_order': 'Voulez-vous vraiment passer la commande ?',
        'are_you_sure_want_to_remove_card': 'Voulez-vous vraiment supprimer cette carte ?',
        'are_you_sure_enable_pooling': 'Êtes-vous sûr de vouloir activer le partage d\'enveloppes ?',
        'edit_credit_card': '<span class="font-extrabold font-italic">Modifier</span> la carte bancaire',
        'remove': 'Supprimer',
        'please_enter_the_number_of_license': 'Entrez le nombre de licences.',
        'are_you_sure_want_to_set_this_member_to_admin': 'Voulez-vous vraiment augmenter le rôle de l\'utilisateur sélectionné au niveau Administrateur ?',
        'are_you_sure_want_to_set_this_admin_to_member': 'Voulez-vous réduire le rôle de l\'utilisateur sélectionné au niveau Membre ?',
        'are_you_sure_want_to_disable_owner_licence': 'Voulez-vous vraiment désactiver votre licence ?',
        'are_you_sure_want_to_recover_owner_licence': 'Voulez-vous vraiment activer votre licence ?',
        'switch_to_annual_billing': '<span class="font-extrabold font-italic">Passer</span> à une facturation annuelle',
        'switch_to_business_billing': '<span class="font-extrabold font-italic">Mettre</span> à niveau l\'abonnement',
        'techsoup_renew': '<span class="font-extrabold font-italic">Renouveler</span> l\'abonnement',
        'buy_connector': '<span class="font-extrabold font-italic">Acheter</span> Foxit Connectors',
        'enable_pooling': '<span class="font-extrabold font-italic">Activer</span> le Partage d\'Enveloppe',
        'are_you_sure_want_to_transfer_to_the_recipient': 'Voulez-vous vraiment migrer le service d\'abonnement lié au compte actuel vers le nouveau compte : {email}',
        'are_you_sure_want_to_change_the_role_to_setup_admin': 'Voulez-vous vraiment <span class="modal-title" style="font-weight: 600">changer le rôle en administrateur de configuration</span> ? L\'administrateur de configuration peut ajouter des membres et attribuer des licences, ainsi que gérer les paramètres de l\'entreprise, mais n\'occupe pas de licence et n\'a pas accès à l\'utilisation du produit.',
        'are_you_sure_want_to_change_the_role_to_member': 'Voulez-vous vraiment <span class="font-extrabold" style="font-weight: 600">changer le rôle en membre</span> ? Le membre est uniquement autorisé à utiliser le produit.',
        'envelop_pooling_notice': 'Get our Recommended Envelope Pooling to seamlessly share templates, signature workflows, contact lists, bulk sending lists, and company branding across your organization. ',
        'envelop_pooling_license_num_notice': 'Le montant total du regroupement d\'enveloppes dépasse le nombre maximal de vos licences d\'abonnement.',
        'cancel_sub_reason_notice': 'Nous sommes désolés que vous envisagiez de nous quitter. Pourriez-vous nous dire pourquoi ?',
        'cancel_sub_month_to_yearly_notice': 'Pour annuler votre abonnement, vous devez attendre que votre plan annuel soit terminé.',
        'need_select_a_reason_for_cancel_sub_notice': 'Veuillez sélectionner la raison de l\'annulation de votre abonnement.',
        'cancel_my_subscription': 'Annuler le renouvellement automatique',
        'keep_my_subscription': 'Maintenir le renouvellement automatique',
        'are_you_sure_want_to_remove_setup_admin': 'Voulez-vous vraiment supprimer cet administrateur de configuration ?',
        'are_you_sure_want_to_upgrade_order': 'Voulez-vous vraiment mettre à niveau le plan d\'abonnement ?',
        'do_not_offer_yearly_paid_monthly_notice': 'Nous n\'offrons actuellement pas d\'abonnement "Annuel, payé mensuellement". Veuillez passer au plan annuel avant d\'acheter des abonnements supplémentaires.',
        'do_not_offer_monthly_paid_monthly_notice': 'Nous n\'offrons actuellement pas d\'abonnement "Une fois par mois". Veuillez passer au plan annuel avant d\'acheter des abonnements supplémentaires.',
    },
    // date range picker
    dateRangePicker: {
        locale: {
            applyLabel: 'Appliquer le code',
            fromLabel: 'De',
            toLabel: 'à',
            customRangeLabel: 'Plage personnalisée',
            daysOfWeek: ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam'],
            monthNames: ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'],
            firstDay: 0
        }
    },
    // 上传
    upload: {
        'you_have_cancelled_the_update': 'You have cancelled the update!',
        'failed_to_install': 'Failed to install.',
        'installation_has_succeed_please_refresh_current_page': 'Installation has succeed please refresh current page.',
        'web_uploader_dont_support_your_browser': 'Web Uploader don\'t support your browser!',
        'rotate_right': 'Rotate to right',
        'rotate_left': 'Rotate to left',
        'file_size_exceed': 'The Upload File Size Has Exceed',
        'file_upload_interrupt': 'The Upload Has Interrupt',
        'upload_failed_please_retry': 'Upload Failed, Please Retry',
        'previewing': 'Previewing',
        'unable_to_preview': 'Aperçu impossible',
        'something_has_gone_wrong_during_previewing': 'Something has gone wrong during previewing',
        'suspend_to_upload': 'Suspend to upload',
        'continue_to_upload': 'Continue to upload',
        'begin_to_upload': 'Begin to upload',
        'file_type_is_error': 'The upload file type is not allow',
        'duplicate_file_upload': 'Téléchargement de fichier en double',
        'continue_to_add': 'Continuer à ajouter',
        'upload_file_number_has_exceed': 'Le nombre de fichiers téléchargés a dépassé',
        // 上传描述
        funcDesc: function (type, params) {
            let desc = '';
            switch (type) {
                case 'upload_ready':
                    desc += 'You have selected ' + params.fileCount + ' files, total size: ' + params.totalSize;
                    break;
                case 'upload_confirm':
                    desc += 'Téléchargement réussi pour ' + params.successNum + ' fichiers, échec de téléchargement pour ' + params.FailNum + ' fichiers. <a class="retry" href="#">Re-télécharger</a> les fichiers en échec ou les <a class="ignore" href="#">ignorer</a>.';
                    break;
                case 'upload_finish':
                    desc += 'Total: ' + params.total + ' fichiers, Succès: ' + params.successNum;
                    if (params.FailNum) {
                        desc += ', Failed: ' + params.FailNum;
                    }
                    break;
                case 'exceed_num_limit':
                    desc += 'Le nombre maximum de fichiers à télécharger est de ' + params.max;
                    break;
                case 'exceed_file_size':
                    desc += 'La taille maximale des fichiers téléchargeables est limitée à ' + params.max + 'MB';
                    break;
            }

            return desc;
        },
    },
    register:{
        'trial_esign_content': 'Foxit PDF Editor est parfaitement adapté à Foxit eSign Essentials. Foxit PDF Editor est intégré à Foxit eSign Essentials pour fournir une application unique permettant de créer, modifier, remplir et signer électroniquement des documents.',
        'trial_pdf_editor_content' : 'Foxit eSign est parfaitement adapté à Foxit PDF Editor.  Foxit PDF Editor est intégré à Foxit eSign pour fournir une application unique permettant de créer, modifier, remplir et signer électroniquement des documents.',
        'trial_esign_btn_ok':'Version d\'évaluation de Foxit eSign Essentials',
        'trial_esign_btn_close':'Ne pas essayer et fermer',
        'download_pdf_editor_btn_ok' : 'Télécharger PDF Editor',
    },
    editorCloud: {
        'note': 'Note',
        'the_fie_size_10MB': 'Le taille du fichier dépasse la limite de téléchargement de 10Mo.',
        'sorry_the_file': 'Sorry, the file type is not supported',

        funcDesc: function (showSize) {
            let desc = '';
            desc += 'Téléchargement du fichier de ' + showSize + ' en cours...';
            return desc;
        },
    }
};
