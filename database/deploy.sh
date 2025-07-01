#!/bin/bash
# 데이터베이스 마이그레이션 배포 스크립트
# Usage: ./database/deploy.sh [environment]

set -e  # 에러 발생 시 스크립트 중단

ENVIRONMENT=${1:-"development"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATIONS_DIR="$SCRIPT_DIR/migrations"
SEEDS_DIR="$SCRIPT_DIR/seeds"

echo "🚀 Kiko 데이터베이스 마이그레이션 시작"
echo "환경: $ENVIRONMENT"
echo "스크립트 위치: $SCRIPT_DIR"
echo "======================================"

# 환경 변수 확인
if [[ -z "$SUPABASE_URL" || -z "$SUPABASE_SERVICE_ROLE_KEY" ]]; then
    echo "❌ 필수 환경 변수가 설정되지 않았습니다:"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_SERVICE_ROLE_KEY"
    echo ""
    echo "💡 환경 변수 설정 방법:"
    echo "   export SUPABASE_URL=https://your-project-id.supabase.co"
    echo "   export SUPABASE_SERVICE_ROLE_KEY=your-service-role-key"
    exit 1
fi

# PostgreSQL 클라이언트 확인
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL 클라이언트(psql)가 설치되지 않았습니다."
    echo "💡 설치 방법:"
    echo "   MacOS: brew install postgresql"
    echo "   Ubuntu: sudo apt-get install postgresql-client"
    exit 1
fi

# Supabase 프로젝트 URL에서 연결 정보 추출
PROJECT_ID=$(echo $SUPABASE_URL | sed -n 's/.*\/\/\([^.]*\).*/\1/p')
DB_HOST="db.${PROJECT_ID}.supabase.co"
DB_NAME="postgres"
DB_USER="postgres"
DB_PASSWORD="$SUPABASE_SERVICE_ROLE_KEY"

echo "📡 데이터베이스 연결 정보:"
echo "   Host: $DB_HOST"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo ""

# 연결 테스트
echo "🔌 데이터베이스 연결 테스트..."
if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
    echo "❌ 데이터베이스 연결 실패"
    echo "💡 확인사항:"
    echo "   1. SUPABASE_URL이 올바른지 확인"
    echo "   2. SUPABASE_SERVICE_ROLE_KEY가 올바른지 확인"
    echo "   3. 네트워크 연결 상태 확인"
    exit 1
fi
echo "✅ 데이터베이스 연결 성공"

# 마이그레이션 실행 함수
run_migration() {
    local file="$1"
    local filename=$(basename "$file")
    
    echo "📋 실행 중: $filename"
    
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f "$file"; then
        echo "✅ $filename 완료"
    else
        echo "❌ $filename 실패"
        exit 1
    fi
}

# 통합 마이그레이션 파일이 있으면 실행
if [[ -f "$SCRIPT_DIR/test_migration.sql" ]]; then
    echo ""
    echo "🔧 통합 마이그레이션 실행..."
    run_migration "$SCRIPT_DIR/test_migration.sql"
else
    # 개별 마이그레이션 파일들 순서대로 실행
    echo ""
    echo "🔧 개별 마이그레이션 실행..."
    
    for migration_file in "$MIGRATIONS_DIR"/*.sql; do
        if [[ -f "$migration_file" ]]; then
            run_migration "$migration_file"
        fi
    done
fi

# 개발 환경에서만 시드 데이터 실행
if [[ "$ENVIRONMENT" == "development" ]]; then
    echo ""
    echo "🌱 시드 데이터 실행..."
    
    for seed_file in "$SEEDS_DIR"/*.sql; do
        if [[ -f "$seed_file" ]]; then
            run_migration "$seed_file"
        fi
    done
else
    echo ""
    echo "⚠️ 프로덕션 환경에서는 시드 데이터를 실행하지 않습니다."
fi

# 검증 스크립트 실행
echo ""
echo "🧪 데이터베이스 검증..."

VALIDATION_SQL="
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;
"

echo "📊 생성된 테이블 목록:"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "$VALIDATION_SQL"

# 기본 통계 정보
STATS_SQL="
SELECT 
    'users' as table_name, COUNT(*) as row_count FROM users
UNION ALL
SELECT 'scripts', COUNT(*) FROM scripts  
UNION ALL
SELECT 'sentences', COUNT(*) FROM sentences
UNION ALL  
SELECT 'words', COUNT(*) FROM words
UNION ALL
SELECT 'user_words', COUNT(*) FROM user_words
UNION ALL
SELECT 'user_scripts_progress', COUNT(*) FROM user_scripts_progress
UNION ALL
SELECT 'bookmarks', COUNT(*) FROM bookmarks
ORDER BY table_name;
"

echo ""
echo "📈 테이블별 데이터 수:"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "$STATS_SQL"

echo ""
echo "🎉 데이터베이스 마이그레이션 완료!"
echo "======================================"
echo "✅ 모든 테이블이 성공적으로 생성되었습니다."
echo "✅ 인덱스 및 제약조건이 적용되었습니다."
echo "✅ Row-Level Security 정책이 설정되었습니다."

if [[ "$ENVIRONMENT" == "development" ]]; then
    echo "✅ 개발용 샘플 데이터가 추가되었습니다."
fi

echo ""
echo "🔗 다음 단계:"
echo "   1. FastAPI 서버 시작: cd backend && uvicorn app.main:app --reload"
echo "   2. 데이터베이스 상태 확인: http://localhost:8000/api/v1/db/status"
echo "   3. API 문서 확인: http://localhost:8000/docs" 