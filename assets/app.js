/* 서비스 워커 등록 — 오프라인으로 읽기 위한 준비.
   register()의 경로는 이 스크립트가 아니라 '페이지' 기준으로 풀린다.
   자료는 topics/NN-.../ 안에 있고 목차는 루트에 있어서 깊이가 다르므로,
   이 파일의 위치(assets/)에서 거꾸로 계산해 어느 페이지에서 불러도 같은 곳을 가리키게 한다. */
(function () {
  if (!('serviceWorker' in navigator)) return;   /* 지원 안 하면 그냥 온라인으로 본다 */
  var here = document.currentScript && document.currentScript.src;
  if (!here) return;
  var swUrl = new URL('../sw.js', here);         /* assets/ 의 한 단계 위 = 사이트 루트 */
  window.addEventListener('load', function () {
    navigator.serviceWorker.register(swUrl).catch(function (err) {
      console.warn('[sw] 등록 실패:', err);
    });
  });
})();
