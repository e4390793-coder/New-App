import io

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image, UnidentifiedImageError


st.set_page_config(
    page_title="Chart Screenshot Analyzer",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Chart Screenshot Analyzer")
st.caption("স্ক্রিনশট দেখা ও শিক্ষামূলক হিসাবের জন্য—ট্রেডিং সিগন্যাল বা অটো-ট্রেডার নয়।")

st.warning(
    "সতর্কতা: এই অ্যাপ স্ক্রিনশটে রঙের পিক্সেল বিশ্লেষণ করে মাত্র। "
    "এটি ক্যান্ডেল, trend, market direction বা ভবিষ্যৎ price নির্ভরযোগ্যভাবে শনাক্ত করে না। "
    "কোনো ফলাফলকে ট্রেড সিগন্যাল হিসেবে ব্যবহার করবেন না।"
)

tab_chart, tab_risk = st.tabs(["স্ক্রিনশট বিশ্লেষণ", "ঝুঁকির হিসাব"])


with tab_chart:
    uploaded_file = st.file_uploader(
        "চার্টের স্ক্রিনশট আপলোড করুন",
        type=["png", "jpg", "jpeg", "webp"],
    )

    if uploaded_file is None:
        st.info("শুরু করতে একটি চার্টের স্ক্রিনশট আপলোড করুন।")
    else:
        try:
            image = Image.open(uploaded_file).convert("RGB")
        except (UnidentifiedImageError, OSError):
            st.error("ছবিটি খোলা যায়নি। অন্য PNG বা JPG ফাইল দিয়ে চেষ্টা করুন।")
            st.stop()

        image_array = np.asarray(image)
        height, width, _ = image_array.shape

        st.write(f"ছবির আকার: **{width} × {height} px**")

        left, right = st.columns(2)
        with left:
            st.image(image, caption="আপলোড করা স্ক্রিনশট", use_container_width=True)

        st.subheader("বিশ্লেষণের এলাকা নির্বাচন")
        st.caption(
            "স্লাইডার দিয়ে চার্টের অংশ বাছুন। পুরো স্ক্রিনশট নির্বাচন করলে "
            "বোতাম বা অন্য UI-এর রংও ফলাফলে ঢুকে যেতে পারে।"
        )

        x1, x2 = st.slider(
            "অনুভূমিক এলাকা (X)",
            min_value=0,
            max_value=width,
            value=(0, width),
        )
        y1, y2 = st.slider(
            "উল্লম্ব এলাকা (Y)",
            min_value=0,
            max_value=height,
            value=(0, height),
        )

        settings_left, settings_right = st.columns(2)
        with settings_left:
            saturation_threshold = st.slider(
                "রঙের স্পষ্টতার সীমা",
                min_value=0,
                max_value=255,
                value=75,
                help="এটি বাড়ালে ফিকে বা ধূসর রঙের পিক্সেল বাদ পড়তে পারে।",
            )
        with settings_right:
            brightness_threshold = st.slider(
                "উজ্জ্বলতার সীমা",
                min_value=0,
                max_value=255,
                value=45,
                help="এটি কম উজ্জ্বল পিক্সেল বাদ দিতে সাহায্য করে।",
            )

        if x2 <= x1 or y2 <= y1:
            st.error("বিশ্লেষণের জন্য বৈধ এলাকা নির্বাচন করুন।")
        else:
            crop = image.crop((x1, y1, x2, y2))
            crop_array = np.asarray(crop)
            hsv = np.asarray(crop.convert("HSV"))

            hue = hsv[:, :, 0].astype(np.int16)
            saturation = hsv[:, :, 1].astype(np.int16)
            brightness = hsv[:, :, 2].astype(np.int16)

            colorful = (
                (saturation >= saturation_threshold)
                & (brightness >= brightness_threshold)
            )

            # PIL-এর HSV hue মান 0–255 রেঞ্জে থাকে।
            # এই সীমাগুলো কেবল আনুমানিক রঙ শনাক্ত করে; ক্যান্ডেল শনাক্ত করে না।
            red_mask = colorful & ((hue <= 12) | (hue >= 245))
            green_mask = colorful & (hue >= 55) & (hue <= 145)

            red_count = int(red_mask.sum())
            green_count = int(green_mask.sum())
            total_pixels = int(crop_array.shape[0] * crop_array.shape[1])
            other_count = max(total_pixels - red_count - green_count, 0)
            classified_count = red_count + green_count

            st.image(crop, caption="নির্বাচিত বিশ্লেষণ এলাকা", use_container_width=True)

            metric1, metric2, metric3 = st.columns(3)
            metric1.metric("শনাক্ত লাল পিক্সেল", f"{red_count:,}")
            metric2.metric("শনাক্ত সবুজ পিক্সেল", f"{green_count:,}")
            metric3.metric("অন্য/শনাক্ত নয়", f"{other_count:,}")
                      if classified_count == 0:
                st.info(
                    "এই এলাকায় নির্ধারিত সীমা অনুযায়ী লাল বা সবুজ পিক্সেল পাওয়া যায়নি। "
                    "চার্টের রং আলাদা হলে সেটিংস বদলে আবার দেখুন।"
                )
            else:
                red_share = 100 * red_count / classified_count
                green_share = 100 * green_count / classified_count

                a, b = st.columns(2)
                a.metric("শনাক্ত লাল অংশ", f"{red_share:.1f}%")
                b.metric("শনাক্ত সবুজ অংশ", f"{green_share:.1f}%")

                if green_share > red_share:
                    st.info("নির্বাচিত ছবির অংশে সবুজ পিক্সেল বেশি—এটি বাজারের দিক বা BUY সিগন্যাল নয়।")
                elif red_share > green_share:
                    st.info("নির্বাচিত ছবির অংশে লাল পিক্সেল বেশি—এটি বাজারের দিক বা SELL সিগন্যাল নয়।")
                else:
                    st.info("নির্বাচিত অংশে লাল ও সবুজ পিক্সেলের সংখ্যা সমান।")

            st.subheader("ছবির বাম থেকে ডানে রঙের বণ্টন")
            segment_count = st.slider(
                "বিভাগের সংখ্যা",
                min_value=5,
                max_value=100,
                value=25,
            )

            crop_width = crop_array.shape[1]
            boundaries = np.linspace(0, crop_width, segment_count + 1, dtype=int)
            rows = []

            for i in range(segment_count):
                start = boundaries[i]
                end = boundaries[i + 1]

                if end <= start:
                    continue

                segment_red = int(red_mask[:, start:end].sum())
                segment_green = int(green_mask[:, start:end].sum())
                segment_total = segment_red + segment_green

                if segment_total:
                    segment_red_pct = 100 * segment_red / segment_total
                    segment_green_pct = 100 * segment_green / segment_total
                else:
                    segment_red_pct = 0.0
                    segment_green_pct = 0.0

                rows.append(
                    {
                        "বিভাগ": i + 1,
                        "লাল পিক্সেল (%)": segment_red_pct,
                        "সবুজ পিক্সেল (%)": segment_green_pct,
                    }
                )

            if rows:
                distribution = pd.DataFrame(rows)
                st.line_chart(
                    distribution,
                    x="বিভাগ",
                    y=["লাল পিক্সেল (%)", "সবুজ পিক্সেল (%)"],
                )
                st.dataframe(distribution, use_container_width=True, hide_index=True)

                csv_data = distribution.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "রঙের বণ্টনের CSV ডাউনলোড",
                    data=csv_data,
                    file_name="chart_color_distribution.csv",
                    mime="text/csv",
                )

            st.caption(
                "চার্টের থিম, ক্যান্ডেলের রং, indicator, grid, background এবং স্ক্রিনশটের "
                "মান এই ফলাফল বদলে দিতে পারে। এটি ক্যান্ডেল বা trend analysis নয়।"
            )


with tab_risk:
    st.subheader("Binary payout-এর ব্রেক-ইভেন ও সম্ভাব্য ঝুঁকি")
    st.caption(
        "এটি কেবল গাণিতিক উদাহরণ। payout বদলাতে পারে; হিসাবটি লাভ বা ফলাফলের পূর্বাভাস নয়।"
    )

    c1, c2 = st.columns(2)

    with c1:
        stake = st.number_input(
            "প্রতি ট্রেডে stake",
            min_value=0.01,
            value=1.0,
            step=0.5,
        )
        payout_percent = st.number_input(
            "জিতলে লাভের payout (%)",
            min_value=0.0,
            max_value=1000.0,
            value=80.0,
            step=1.0,
        )

    with c2:
        trade_count = st.number_input(
            "উদাহরণে ট্রেডের সংখ্যা",
            min_value=1,
            max_value=10000,
            value=5,
            step=1,
        )
        assumed_win_rate = st.number_input(
            "শুধু উদাহরণের জন্য অনুমিত win rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=50.0,
                        step=1.0,
        )

    payout = payout_percent / 100
    win_rate = assumed_win_rate / 100

    if payout > 0:
        breakeven_rate = 100 / (1 + payout)
        st.metric("গাণিতিক ব্রেক-ইভেন win rate", f"{breakeven_rate:.2f}%")
    else:
        st.metric("গাণিতিক ব্রেক-ইভেন win rate", "payout 0% হলে হিসাব প্রযোজ্য নয়")

    total_stake = stake * int(trade_count)
    hypothetical_net = stake * (win_rate * payout - (1 - win_rate)) * int(trade_count)

    r1, r2 = st.columns(2)
    r1.metric("সব ট্রেড হারলে মোট stake ঝুঁকিতে", f"{total_stake:.2f}")
    r2.metric("অনুমিত win rate-এ তাত্ত্বিক ফল", f"{hypothetical_net:+.2f}")

    st.warning(
        "অনুমিত win rate আপনি নিজে দিয়েছেন—এটি বাস্তব বা যাচাইকৃত হার নয়। "
        "ব্রেক-ইভেন হিসাবেও fees, payout পরিবর্তন, execution সমস্যা ও অন্যান্য ঝুঁকি ধরা হয়নি। "
        "হারাতে পারবেন না এমন অর্থ ঝুঁকিতে দেবেন না।"
    )
          
