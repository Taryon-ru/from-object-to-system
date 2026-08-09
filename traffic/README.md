# В ветке traffic-data
cat > README.md << 'EOF'
# Traffic data

Автоматическая статистика репозитория `taryon-ru/from-object-to-system`.

<table align="center">
  <tr>
    <td align="center" width="50%">
      <img
        src="https://raw.githubusercontent.com/taryon-ru/from-object-to-system/traffic-data/traffic/charts/views.svg"
        alt="GitHub views"
        width="100%"
      />
    </td>
    <td align="center" width="50%">
      <img
        src="https://raw.githubusercontent.com/taryon-ru/from-object-to-system/traffic-data/traffic/charts/clones.svg"
        alt="GitHub clones"
        width="100%"
      />
    </td>
  </tr>
</table>

---

Данные собираются ежедневно через GitHub Traffic API.
История хранится в этой ветке, исходный код генератора — в `main`.
EOF

git add README.md
git commit -m "docs: add README for traffic-data"
git push origin traffic-data

git checkout main
