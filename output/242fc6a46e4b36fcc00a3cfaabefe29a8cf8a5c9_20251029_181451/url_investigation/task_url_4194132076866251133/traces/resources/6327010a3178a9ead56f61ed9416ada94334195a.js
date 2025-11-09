var foxitApp = {
   REGION_INFO: '',
   DATA_FOR_TRACK: '',
   init: function (params) {
      this.REGION_INFO = params.REGION_INFO || '';
      this.DATA_FOR_TRACK = params.DATA_FOR_TRACK || '';
   },
   getParamUri: () => {
      return atob(foxitApp.PARAM_URI)
   },
};
let dataFilter = {
   number: {
      sum: function (...nums) {
         let sum = 0;
         for (let i = 0, len = nums.length; i < len; i++) {
            sum += nums[i]
         }
         if (sum) {
            sum += 0.0000001
         }
         return sum
      },
      fixedSum: function (len, ...nums) {
         let sum = 0;
         for (let i = 0, len = nums.length; i < len; i++) {
            sum += nums[i]
         }
         return this.fixed(sum + 0.0000001, len)
      },
      round: function (num, d = 2) {
         return Math.round((parseFloat(num) + Number.EPSILON) * Math.pow(10, d)) / Math.pow(10, d)
      },
      checkPostInt: function (value) {
         return /(^[1-9]\d*$)/.test(value)
      },
      checkNatural: function (value) {
         return /^0$|(^[1-9]\d*$)/.test(value)
      },
      fixed: function (val, len, round) {
         len = isNaN(len) ? 2 : len;
         round = !dataFilter.isEmpty(round);
         val = Number.parseFloat(val);
         if (typeof val === 'string') {
            val = parseFloat(val)
         }
         if (round) {
            return Number(val + 1 / Math.pow(10, len + 4)).toFixed(len)
         } else {
            return (parseInt(this.numMulti(val, Math.pow(10, len))) / Math.pow(10, len)).toFixed(len)
         }
      },
      fixedAdd: function (a, b, len) {
         len = isNaN(len) ? 2 : len;
         return ((this.numMulti(parseFloat(a), Math.pow(10, len)) + this.numMulti(parseFloat(b), Math.pow(10, len))) / Math.pow(10, len)).toFixed(len)
      },
      numSub: function (num1, num2) {
         let r1, r2, m, n;
         try {
            r1 = num1.toString().split('.')[1].length
         } catch (e) {
            r1 = 0
         }
         try {
            r2 = num2.toString().split('.')[1].length
         } catch (e) {
            r2 = 0
         }
         m = Math.pow(10, Math.max(r1, r2));
         n = (r1 >= r2) ? r1 : r2;
         return parseFloat(((num1 * m - num2 * m) / m).toFixed(n))
      },
      numMulti: function (num1, num2) {
         let baseNum = 0;
         try {
            baseNum += num1.toString().split(".")[1].length
         } catch (e) { }
         try {
            baseNum += num2.toString().split(".")[1].length
         } catch (e) { }
         return Number(num1.toString().replace(".", "")) * Number(num2.toString().replace(".", "")) / Math.pow(10, baseNum)
      },
      numMultiArr: function (num, numArr, round = !0) {
         let total = 0;
         num = parseFloat(num);
         for (let i = 0; i < numArr.length; i++) {
            total += parseFloat(dataFilter.number.fixed(num * parseFloat(numArr[i]), 2, !0))
         }
         return total
      },
      numDivide: function (num1, num2) {
         let baseNum = 0;
         try {
            baseNum += num1.toString().split(".")[1].length
         } catch (e) { }
         try {
            baseNum += num2.toString().split(".")[1].length
         } catch (e) { }
         return dataFilter.number.fixed((num1 / num2) + 0.0000001, 2)
      },
      fmtMoney: function (s, n, c, cs, g, lang) {
         lang = lang || 'en-us';
         n = n > 0 && n <= 20 ? n : 2;
         s = parseFloat((s + '').replace(/[^\d\.-]/g, '')).toFixed(n) + '';
         let configForUSD = {
            'en-us': {
               p: 'b',
               t: ',',
               c: '.',
               g: '',
               code: '$'
            },
            'ru-ru': {
               p: 'b',
               t: '',
               c: ',',
               g: '',
               code: '$'
            },
            'es-la': {
               p: 'b',
               t: '',
               c: ',',
               g: ' ',
               code: '$'
            },
            'pt-br': {
               p: 'b',
               t: '.',
               c: ',',
               g: ' ',
               code: '$'
            },
            'fr-fr': {
               p: 'a',
               t: ' ',
               c: ',',
               g: ' ',
               code: '$'
            },
            'de-de': {
               p: 'a',
               t: '.',
               c: ',',
               g: ' ',
               code: '$'
            },
            'nl-nl': {
               p: 'b',
               t: '',
               c: ',',
               g: ' ',
               code: '$'
            },
            'pt-pt': {
               p: 'a',
               t: '.',
               c: ',',
               g: ' ',
               code: '$'
            },
            'it-it': {
               p: 'b',
               t: '.',
               c: ',',
               g: ' ',
               code: '$'
            },
            'pl-pl': {
               p: 'a',
               t: '',
               c: ',',
               g: ' ',
               code: '$'
            },
         };
         let configForEUR = {
            'en-us': {
               p: 'b',
               t: ',',
               c: '.',
               g: '',
               code: '€'
            },
            'ru-ru': {
               p: 'b',
               t: '',
               c: ',',
               g: '',
               code: '€'
            },
            'es-la': {
               p: 'b',
               t: '',
               c: ',',
               g: '',
               code: '€'
            },
            'pt-br': {
               p: 'b',
               t: '.',
               c: ',',
               g: '',
               code: '€'
            },
            'fr-fr': {
               p: 'a',
               t: ' ',
               c: ',',
               g: '',
               code: '€'
            },
            'de-de': {
               p: 'a',
               t: '.',
               c: ',',
               g: '',
               code: '€'
            },
            'nl-nl': {
               p: 'b',
               t: '',
               c: ',',
               g: ' ',
               code: '€'
            },
            'pt-pt': {
               p: 'a',
               t: '.',
               c: ',',
               g: ' ',
               code: '€'
            },
            'it-it': {
               p: 'a',
               t: '.',
               c: ',',
               g: '',
               code: '€'
            },
            'pl-pl': {
               p: 'a',
               t: '',
               c: ',',
               g: ' ',
               code: '€'
            },
         };
         let configForCommon = {
            'en-us': {
               p: 'b',
               t: ',',
               c: '.',
               g: '',
               code: cs
            },
            'ru-ru': {
               p: 'b',
               t: '',
               c: ',',
               g: '',
               code: cs
            },
            'es-la': {
               p: 'b',
               t: '',
               c: ',',
               g: ' ',
               code: cs
            },
            'pt-br': {
               p: 'b',
               t: '.',
               c: ',',
               g: ' ',
               code: cs
            },
            'fr-fr': {
               p: 'b',
               t: ' ',
               c: ',',
               g: ' ',
               code: cs
            },
            'de-de': {
               p: 'b',
               t: '.',
               c: ',',
               g: ' ',
               code: cs
            },
            'nl-nl': {
               p: 'b',
               t: '',
               c: ',',
               g: ' ',
               code: cs
            },
            'pt-pt': {
               p: 'b',
               t: '.',
               c: ',',
               g: ' ',
               code: cs
            },
            'it-it': {
               p: 'b',
               t: '.',
               c: ',',
               g: ' ',
               code: cs
            },
            'pl-pl': {
               p: 'b',
               t: '',
               c: ',',
               g: ' ',
               code: cs
            },
         };
         let config = {};
         if (c === 'usd' || c === 'USD') {
            config = configForUSD
         } else if (c === 'eur' || c === 'EUR') {
            config = configForEUR
         } else {
            config = configForCommon
         }
         let l = s.split('.')[0].split('').reverse();
         let r = s.split('.')[1];
         let t = '';
         for (let i = 0; i < l.length; i++) {
            t += l[i] + ((i + 1) % 3 === 0 && (i + 1) !== l.length ? config[lang].t : '')
         }
         if (config[lang].p === 'b') {
            return config[lang].code + config[lang].g + t.split('').reverse().join('') + config[lang].c + r
         } else {
            return t.split('').reverse().join('') + config[lang].c + r + config[lang].g + config[lang].code
         }
      },
      reverseFmtMoney: function (s) {
         return parseFloat(s.replace(/[^\d\.-]/g, ''))
      },
   },
   string: {
      checkAaNumSpChars: function (value, spChars = '') {
         let regObj;
         if (spChars === '') {
            regObj = new RegExp("^[A-Za-z0-9]+$")
         } else {
            regObj = new RegExp("^[A-Za-z0-9" + spChars + "]+$")
         }
         return regObj.test(value)
      },
      isEmail: function (val) {
         let reEmail = /^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/;
         return reEmail.test(val)
      },
      trim: function (val) {
         if (val === "") {
            return val
         } else {
            return val.replace(/^\s+|\s+$/g, "")
         }
      },
      isHttp: function (val) {
         let reg = /^(https?:\/\/)([0-9a-z.]+)(:[0-9]+)?([/0-9a-z.]+)?(\?[0-9a-z&=]+)?(#[0-9-a-z]+)?/i;
         return reg.test(val)
      },
      httpBuildQuery: function (obj) {
         let str = '',
            k = '',
            val = '';
         for (let e in obj) {
            if (str === '') {
               if (e === 'meta_data') {
                  for (let ee in obj[e]) {
                     if (str === '') {
                        str += 'meta_data[' + ee + ']=' + obj[e][ee]
                     } else {
                        str += '&meta_data[' + ee + ']=' + obj[e][ee]
                     }
                  }
               } else {
                  str += e + '=' + obj[e]
               }
            } else {
               if (e === 'meta_data') {
                  for (let ee in obj[e]) {
                     str += '&meta_data[' + ee + ']=' + obj[e][ee]
                  }
               } else {
                  str += '&' + e + '=' + obj[e]
               }
            }
         }
         return str
      },
      basename: function (url) {
         let idx = url.lastIndexOf('/')
         idx = idx > -1 ? idx : url.lastIndexOf('\\')
         if (idx < 0) {
            return url
         }
         return url.substring(idx + 1)
      },
      sanitize: str => {
         let div = document.createElement('div');
         div.textContent = str;
         return div.innerHTML
      }
   },
   length: function (val) {
      if (val instanceof Array) {
         return val.length
      } else if (typeof val === 'object') {
         return Object.getOwnPropertyNames(val).length
      }
   },
   object: {
      isNull: function (val) {
         return JSON.stringify(val) === "{}"
      },
      isObject: function (val) {
         return (typeof val) === 'object'
      },
      length: function (val) {
         return Object.getOwnPropertyNames(val).length
      },
      objectKeys: function (obj, keyName = 'key') {
         let list = [];
         for (let i = 0; i < obj.length; i++) {
            list.push(obj[i][keyName])
         }
         return list
      },
      keys: function (obj) {
         return Object.keys(obj)
      },
      copy: function (obj, type = 'json') {
         let newObj = null;
         switch (type) {
            case 'json':
               newObj = JSON.parse(JSON.stringify(obj));
               break;
            default:
               newObj = obj
         }
         return newObj
      },
      isEqual: function (objA, objB) {
         return JSON.stringify(objA) === JSON.stringify(objB)
      },
      checkNested: function (obj) {
         if (this.isObject(obj) === !1) {
            return !1
         }
         var args = Array.prototype.slice.call(arguments, 1);
         for (var i = 0; i < args.length; i++) {
            if (!obj || !obj.hasOwnProperty(args[i])) {
               return !1
            }
            obj = obj[args[i]]
         }
         return !0
      }
   },
   isUndef: function (val) {
      return (typeof val) === 'undefined'
   },
   isNull: function (val) {
      return (val === '' || (typeof val) === 'undefined' || val === null)
   },
   isEmpty: function (val) {
      return val === '' || (typeof val) === 'undefined' || val === null || JSON.stringify(val) === '{}' || JSON.stringify(val) === '[]' || val === !1
   },
   ____isObjectAttrEmpty: function (val) { },
   hello: function () {
      alert('world')
   },
   array: {
      inArray: function (needle, haystack) {
         for (let i = 0; i < haystack.length; i++) {
            if (haystack[i] === needle) {
               return !0
            }
         }
         return !1
      },
      arrayKeys: function (array) {
         if (dataFilter.isEmpty(array)) {
            return []
         } else {
            return Object.keys(array)
         }
      },
      filter: function (array) {
         return array.filter(function (e) {
            return e != null
         })
      },
      arrayWalk: function (array, func) {
         if (typeof func !== 'function') {
            return array
         }
         let originalArr = array.concat();
         array.forEach(function (e, i) {
            array[i] = func(originalArr, i, e)
         });
         return array
      },
      getItem: function (arr, k, d) {
         d = d === 'undefined' ? '' : d;
         if (dataFilter.object.checkNested(arr, k)) {
            return arr[k]
         } else {
            return d
         }
      },
      sortBy: function (key, list, type) {
         let temp = null;
         let flag = !1;
         type = type || 'up';
         if (type === 'up') {
            for (let i = 1; i < list.length; i++) {
               for (let k = 0; k < list.length - i; k++) {
                  if (list[k][key] > list[k + 1][key]) {
                     temp = list[k + 1];
                     list[k + 1] = list[k];
                     list[k] = temp;
                     flag = !0
                  }
               }
            }
         } else {
            for (let i = 1; i < list.length; i++) {
               for (let k = 0; k < list.length - i; k++) {
                  if (list[k][key] < list[k + 1][key]) {
                     temp = list[k + 1];
                     list[k + 1] = list[k];
                     list[k] = temp;
                     flag = !0
                  }
               }
            }
         }
         return Object.assign([], list)
      },
      array_column: function (arr, cn) {
         return arr.map(function (value, index) {
            return value[cn]
         })
      },
      array_sum: function (arr) {
         return arr.reduce((partialSum, a) => partialSum + a, 0)
      }
   },
   json: {
      safeParse: function (val) {
         val = val.replace(/\n/g, "\\n").replace(/\r/g, "\\r");
         return JSON.parse(val)
      },
   },
   explode: function (d, s) {
      return s.split(d)
   },
   isSSL: function () {
      return 'https:' === document.location.protocol
   },
   rsaEncrypt: function (text) {
      let encryptObj = new JSEncrypt();
      encryptObj.setPublicKey(metaDataJs.rsaEncryptPk);
      return encryptObj.encrypt(text)
   },
   encFormDataStr: function (slt, fields) {
      let dataArr = slt.serializeArray();
      let str = '';
      Object.keys(dataArr).forEach(function (k) {
         if (dataFilter.array.inArray(dataArr[k].name, fields)) {
            if (str) {
               str += '&' + dataArr[k].name + '=' + encodeURIComponent(dataFilter.rsaEncrypt(dataArr[k].value))
            } else {
               str += dataArr[k].name + '=' + encodeURIComponent(dataFilter.rsaEncrypt(dataArr[k].value))
            }
         } else {
            if (str) {
               str += '&' + dataArr[k].name + '=' + dataArr[k].value
            } else {
               str += dataArr[k].name + '=' + dataArr[k].value
            }
         }
      });
      return str
   }
};