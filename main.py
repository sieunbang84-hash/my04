<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>서울 상권 유망 업종 데이터 대시보드</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Chart.js CDN (데이터 시각화 라이브러리) -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        /* 커스텀 폰트 설정 */
        body { font-family: 'Inter', sans-serif; }
    </style>
</head>
<body class="bg-gray-50 min-h-screen p-4 sm:p-8">

    <!-- Firebase SDK Imports (환경 필수 요구 사항) -->
    <script type="module">
        import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-app.js";
        import { getAuth, signInAnonymously, signInWithCustomToken } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-auth.js";
        import { getFirestore } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";
        import { setLogLevel } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";

        // Firestore 로깅 레벨 설정 (디버깅 목적)
        setLogLevel('Debug');

        // 전역 변수로 Firebase 서비스 인스턴스를 저장합니다.
        let app, db, auth;
        let userId = 'anonymous';

        // 1. Firebase 설정 초기화
        const firebaseConfig = typeof __firebase_config !== 'undefined' ? JSON.parse(__firebase_config) : null;
        const appId = typeof __app_id !== 'undefined' ? __app_id : 'default-app-id';

        if (firebaseConfig) {
            app = initializeApp(firebaseConfig);
            db = getFirestore(app);
            auth = getAuth(app);

            // 2. 인증 처리
            async function authenticate() {
                try {
                    const initialAuthToken = typeof __initial_auth_token !== 'undefined' ? __initial_auth_token : null;
                    if (initialAuthToken) {
                        const userCredential = await signInWithCustomToken(auth, initialAuthToken);
                        userId = userCredential.user.uid;
                        console.log('Signed in with custom token. User ID:', userId);
                    } else {
                        const userCredential = await signInAnonymously(auth);
                        userId = userCredential.user.uid;
                        console.log('Signed in anonymously. User ID:', userId);
                    }
                } catch (error) {
                    console.error("Firebase Authentication failed:", error);
                }
            }

            // 3. 인증 후 데이터 처리 시작
            authenticate().then(() => {
                // Firebase 인증이 완료된 후 메인 데이터 로딩 함수를 호출합니다.
                // 이 함수는 <script> 블록 외부에 정의되어야 전역적으로 접근 가능합니다.
                if (typeof window.loadData === 'function') {
                    window.loadData();
                }
            });
        } else {
             // Firebase 설정이 없는 경우에도 데이터 로딩 시작
             if (typeof window.loadData === 'function') {
                window.loadData();
            }
        }
    </script>


    <!-- 대시보드 UI 시작 -->
    <div id="app" class="max-w-4xl mx-auto space-y-8">
        <header class="text-center p-6 bg-white shadow-lg rounded-xl">
            <h1 class="text-3xl font-extrabold text-blue-700">서울 상권 데이터 분석 대시보드</h1>
            <p class="mt-2 text-gray-600">유망 업종 예측의 근거가 된 핵심 소비 트렌드 시각화</p>
        </header>

        <!-- 로딩 인디케이터 -->
        <div id="loading" class="text-center p-10 bg-white rounded-xl shadow-md">
            <svg class="animate-spin h-8 w-8 text-blue-500 mx-auto mb-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p class="text-gray-500">데이터를 불러오고 분석하는 중...</p>
        </div>

        <!-- 차트 영역 -->
        <div id="charts-container" class="hidden space-y-8">
            
            <div class="bg-white p-6 rounded-xl shadow-lg">
                <h2 class="text-xl font-semibold text-gray-800 mb-4">📈 20·30세대 vs 기타 연령대 매출 기여도</h2>
                <canvas id="ageChart"></canvas>
            </div>

            <div class="bg-white p-6 rounded-xl shadow-lg">
                <h2 class="text-xl font-semibold text-gray-800 mb-4">🗓️ 주중 vs 주말 소비 집중도</h2>
                <canvas id="dayChart"></canvas>
            </div>
            
            <div class="bg-white p-6 rounded-xl shadow-lg">
                <h2 class="text-xl font-semibold text-gray-800 mb-4">🥇 매출액 기준 Top 5 서비스 업종</h2>
                <canvas id="topSectorChart"></canvas>
            </div>
        </div>

        <!-- 에러 메시지 -->
        <div id="error-message" class="hidden text-center p-10 bg-red-100 border border-red-400 text-red-700 rounded-xl shadow-md">
            <p class="font-bold">데이터 로드 실패</p>
            <p>CSV 파일을 불러오는 데 문제가 발생했습니다. 파일명과 경로를 확인해 주세요.</p>
        </div>
        
    </div>

    <script>
        // 전역 변수
        const CSV_FILENAME = "서울시 상권분석서비스(추정매출-자치구).csv";
        const loadingEl = document.getElementById('loading');
        const chartsContainerEl = document.getElementById('charts-container');
        const errorEl = document.getElementById('error-message');

        /**
         * 숫자를 천 단위 콤마 형식으로 변환합니다.
         * @param {number} num - 포맷할 숫자
         * @returns {string} - 콤마가 추가된 문자열
         */
        function formatNumber(num) {
            return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        }

        /**
         * 쉼표로 구분된 CSV 문자열을 객체 배열로 파싱합니다.
         * @param {string} csvText - CSV 파일의 텍스트 내용
         * @returns {Array<Object>} - 파싱된 데이터 객체 배열
         */
        function parseCSV(csvText) {
            const lines = csvText.trim().split('\n');
            if (lines.length === 0) return [];
            
            // 헤더 추출 (첫 번째 줄)
            const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
            const data = [];

            // 데이터 행 파싱 (두 번째 줄부터)
            for (let i = 1; i < lines.length; i++) {
                const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''));
                if (values.length !== headers.length) continue;

                const row = {};
                headers.forEach((header, index) => {
                    // 숫자 데이터를 파싱합니다.
                    if (header.includes('매출_금액') || header.includes('매출_건수')) {
                        row[header] = parseInt(values[index]) || 0;
                    } else {
                        row[header] = values[index];
                    }
                });
                data.push(row);
            }
            return data;
        }

        /**
         * CSV 데이터를 불러와서 분석하고 차트를 그립니다.
         */
        window.loadData = async function() {
            loadingEl.classList.remove('hidden');
            chartsContainerEl.classList.add('hidden');
            errorEl.classList.add('hidden');

            try {
                // 파일 맵을 통해 CSV 파일의 URL을 가져옵니다. (환경에 따라 작동 방식이 다를 수 있음)
                const fileMap = typeof __data_file_map !== 'undefined' ? __data_file_map : {};
                let fileUrl = fileMap[CSV_FILENAME] || CSV_FILENAME;

                // FIX: 파일 이름에 한글이나 특수문자가 포함된 경우 URL 인코딩을 적용하여 fetch 오류를 해결합니다.
                if (fileMap[CSV_FILENAME]) {
                    // __data_file_map에서 URL을 가져온 경우, 파일 이름 부분만 다시 인코딩하여 안전한 URL을 생성합니다.
                    const originalUrl = fileMap[CSV_FILENAME];
                    const encodedFilename = encodeURIComponent(CSV_FILENAME);
                    // 파일 경로의 마지막 부분(인코딩되지 않은 파일 이름)을 인코딩된 파일 이름으로 대체합니다.
                    fileUrl = originalUrl.replace(CSV_FILENAME, encodedFilename);
                }
                
                const response = await fetch(fileUrl);
                if (!response.ok) throw new Error('파일 로드 실패: ' + response.statusText);

                const csvText = await response.text();
                const rawData = parseCSV(csvText);

                if (rawData.length === 0) {
                    throw new Error("데이터가 비어 있습니다.");
                }

                const analyzedData = analyzeData(rawData);
                renderCharts(analyzedData);

                loadingEl.classList.add('hidden');
                chartsContainerEl.classList.remove('hidden');

            } catch (error) {
                console.error("데이터 처리 오류:", error);
                loadingEl.classList.add('hidden');
                errorEl.classList.remove('hidden');
            }
        };


        /**
         * 로드된 데이터를 분석하여 차트용 객체로 만듭니다.
         * @param {Array<Object>} data - 파싱된 CSV 데이터
         * @returns {Object} - 분석 결과 객체
         */
        function analyzeData(data) {
            let totalSales = {
                '20대': 0,
                '30대': 0,
                '10대+40대+50대+60대이상': 0, // 기타 연령대
                '주중': 0,
                '주말': 0
            };

            const sectorSales = {};

            data.forEach(row => {
                // 1. 연령대별 매출
                totalSales['20대'] += row['연령대_20_매출_금액'] || 0;
                totalSales['30대'] += row['연령대_30_매출_금액'] || 0;
                
                // 기타 연령대 합산
                // Note: We need to ensure we use the correct column names from the CSV.
                // Assuming column names are consistent with previous analysis attempt.
                totalSales['10대+40대+50대+60대이상'] += (row['연령대_10_매출_금액'] || 0);
                totalSales['10대+40대+50대+60대이상'] += (row['연령대_40_매출_금액'] || 0);
                totalSales['10대+40대+50대+60대이상'] += (row['연령대_50_매출_금액'] || 0);
                totalSales['10대+40대+50대+60대이상'] += (row['연령대_60_이상_매출_금액'] || 0);

                // 2. 주중/주말 매출
                totalSales['주중'] += row['주중_매출_금액'] || 0;
                totalSales['주말'] += row['주말_매출_금액'] || 0;
                
                // 3. 업종별 매출
                const sectorName = row['서비스_업종_코드_명'];
                const salesAmount = row['당월_매출_금액'] || 0;
                
                if (sectorName) {
                    sectorSales[sectorName] = (sectorSales[sectorName] || 0) + salesAmount;
                }
            });
            
            // Top 5 업종 계산
            const sortedSectors = Object.entries(sectorSales)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 5)
                .map(([name, sales]) => ({ name, sales }));

            // 기타 연령대에서 20대와 30대 매출을 다시 제외 (중복 방지)
            // (Note: This step might be redundant if the individual age group columns were used correctly, 
            // but kept for safety if total columns were used in the original calculation)
            // totalSales['10대+40대+50대+60대이상'] -= totalSales['20대'] + totalSales['30대'];


            return { totalSales, sortedSectors };
        }

        /**
         * 분석 결과를 바탕으로 Chart.js를 사용하여 그래프를 그립니다.
         * @param {Object} data - 분석 결과 객체
         */
        function renderCharts(data) {
            const { totalSales, sortedSectors } = data;

            // 1. 연령대별 매출 기여도 차트 (20대, 30대 vs 기타)
            const ageData = {
                labels: ['20대', '30대', '기타 연령대 (10대, 40대 이상)'],
                datasets: [{
                    label: '총 매출 기여 금액 (원)',
                    data: [
                        totalSales['20대'], 
                        totalSales['30대'], 
                        totalSales['10대+40대+50대+60대이상']
                    ],
                    backgroundColor: ['#3b82f6', '#10b981', '#f59e0b'], // Blue, Green, Yellow
                    borderColor: ['#1d4ed8', '#059669', '#d97706'],
                    borderWidth: 1
                }]
            };

            new Chart(document.getElementById('ageChart'), {
                type: 'bar',
                data: ageData,
                options: {
                    responsive: true,
                    indexAxis: 'y', // 수평 막대 그래프
                    plugins: {
                        legend: { display: false },
                        title: { display: true, text: '20·30세대가 서울 상권 매출을 주도하는 모습 확인' }
                    },
                    scales: {
                        x: { 
                            beginAtZero: true, 
                            title: { display: true, text: '매출액 (원)' },
                            // 큰 숫자에 콤마를 넣어 가독성을 높입니다.
                            ticks: {
                                callback: function(value, index, ticks) {
                                    return formatNumber(value);
                                }
                            }
                        }
                    }
                }
            });

            // 2. 주중/주말 소비 집중도 차트
            const dayData = {
                labels: ['주중 매출', '주말 매출'],
                datasets: [{
                    label: '총 매출 금액 (원)',
                    data: [totalSales['주중'], totalSales['주말']],
                    backgroundColor: ['#6366f1', '#ef4444'], // Indigo, Red
                    hoverOffset: 4
                }]
            };

            new Chart(document.getElementById('dayChart'), {
                type: 'doughnut',
                data: dayData,
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'top' },
                        title: { display: true, text: '여가 및 경험 소비에 따른 주말 매출 집중도' },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    if (context.parsed !== null) {
                                        label += formatNumber(context.parsed) + ' 원';
                                    }
                                    return label;
                                }
                            }
                        }
                    }
                }
            });
            
            // 3. Top 5 서비스 업종 차트
            const topSectorData = {
                labels: sortedSectors.map(s => s.name),
                datasets: [{
                    label: '총 매출 금액 (원)',
                    data: sortedSectors.map(s => s.sales),
                    backgroundColor: '#0ea5e9', // Sky Blue
                    borderColor: '#0284c7',
                    borderWidth: 1
                }]
            };
            
            new Chart(document.getElementById('topSectorChart'), {
                type: 'bar',
                data: topSectorData,
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false },
                        title: { display: true, text: '매출액이 가장 높은 상위 5개 서비스 업종' }
                    },
                    scales: {
                        y: { beginAtZero: true, title: { display: true, text: '매출액 (원)' },
                             ticks: {
                                callback: function(value, index, ticks) {
                                    return formatNumber(value);
                                }
                            }
                        }
                    }
                }
            });
        }
    </script>
</body>
</html>
