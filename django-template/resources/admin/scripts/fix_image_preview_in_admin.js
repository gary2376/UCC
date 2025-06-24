$(function () {
    function endsWithAny(suffixes, string) {
        return suffixes.some(function (suffix) {
            return string.endsWith(suffix);
        });
    }

    $('.file-upload a[href]').each(function () {
        let url = $(this).attr('href')
        if (endsWithAny(['.webp', 'jpg', 'jpeg', 'png'], url)) {
            $(this).replaceWith(`<div><img style="width: 200px" src="${url}"></div>`)
        }
    })
})
