import Header from "../components/Header";
import Footer from "../components/Footer";
import SEOTags from "./TrangChu/components/SEOTags";
import SharedRealEstateAnalytics from "./BieuDo/components/SharedRealEstateAnalytics";
import GoogleTag from "../components/GoogleTag";
import { Helmet } from "react-helmet-async";

const realEstateTypesForRent = [
  "Căn hộ chung cư",
  "Nhà ở",
  "Nhà phố",
  "Nhà trọ",
  "Văn phòng",
];

export default function BieuDoGiaThuePage() {
  const pageTitle = "Biểu đồ giá bất động sản cho thuê tại Việt Nam";

  return (
    <>
      <Helmet>
        <title>{`${pageTitle} | giabatdongsan.info.vn`}</title>
        <meta
          name="description"
          content="Theo dõi biến động giá thuê căn hộ, nhà ở, nhà phố và văn phòng tại Việt Nam. Dữ liệu thực tế, biểu đồ so sánh trực quan theo từng khu vực."
        />
        <meta property="og:title" content={pageTitle} />
        <link
          rel="canonical"
          href="https://giabatdongsan.info.vn/bieu-do-gia-cho-thue"
        />
      </Helmet>
      <GoogleTag />
      <Header />
      <SharedRealEstateAnalytics
        pageTitle={pageTitle}
        unitText="(đơn vị: triệu VND/tháng)"
        priceUnit="triệu VND/tháng"
        realEstateTypes={realEstateTypesForRent}
        priceType="Cho thuê"
      />
      <SEOTags />
      <Footer />
    </>
  );
}
