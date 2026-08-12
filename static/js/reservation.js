function triggerAutomation(brand, storeCode, theme, date, time) {
    const todayStr = new Date().toISOString().split('T')[0];

    const runDate = prompt(
        `🎯 [타겟 예약] ${date} ${time}\n\n` +
        `이 예약을 잡기 위해 타이머를 실행할 날짜를 입력하세요 (예: 오픈런 당일):\n` +
        `(기본값: 오늘)`, 
        todayStr
    );
    
    const runTime = prompt(
        `⏰ 타이머를 실행할 시간 (HH:MM) [오픈런 정각 시각 입력]:`, 
        "00:00"
    );
    
    if (!runDate || !runTime) return;

    // 💡 화면에 이미 스크래퍼가 깃허브 주소로 바꿔둔 img 태그의 src를 가져옴
    const btnEvent = event.target;
    const resItem = btnEvent.closest('.res-item');
    const imgTag = resItem ? resItem.querySelector('img') : null;
    const themeImg = imgTag ? imgTag.src : ""; // 스크래퍼가 만든 깃허브 raw URL

    const formData = new URLSearchParams();
    formData.append("brand", brand);
    formData.append("store_code", storeCode);
    formData.append("theme", theme);
    formData.append("date", date);
    formData.append("time", time);
    formData.append("run_date", runDate);
    formData.append("run_time", runTime);
    formData.append("img", themeImg); // 💡 깃허브 주소 그대로 전송

    fetch("/reserve_automation", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData
    })
    .then(async res => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "에러 발생");
        alert(data.message);
        location.reload();
    })
    .catch(err => alert("타이머 설정 실패: " + err.message));
}