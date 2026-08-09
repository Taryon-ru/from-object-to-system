# В ветке traffic-data
cat > README.md << 'EOF'
# Traffic data

Автоматическая статистика репозитория `taryon-ru/from-object-to-system`.

## Views

![Views](traffic/charts/views.svg)

## Clones

![Clones](traffic/charts/clones.svg)

---

Данные собираются ежедневно через GitHub Traffic API.
История хранится в этой ветке, исходный код генератора — в `main`.
EOF

git add README.md
git commit -m "docs: add README for traffic-data"
git push origin traffic-data

git checkout main
