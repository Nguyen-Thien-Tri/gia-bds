import Header from "../components/Header";
import Footer from "../components/Footer";
import SEOTags from "./TrangChu/components/SEOTags";
import SharedRealEstateAnalytics, {
  RealEstateRecord,
} from "./BieuDo/components/SharedRealEstateAnalytics";
import { BDS_colorMap } from "../assets/colors";
import GoogleTag from "../components/GoogleTag";
import { Helmet } from "react-helmet-async";

const realEstateTypesForSale = Object.keys(
  BDS_colorMap,
) as (keyof typeof BDS_colorMap)[];

export default function BieuDoGiaBanPage() {
  const pageTitle = "Biểu đồ giá bất động sản bán tại Việt Nam";

  return (
    <>
      <Helmet>
        <title>{`${pageTitle} | giabatdongsan.info.vn`}</title>
        <meta
          name="description"
          content="Xem biểu đồ giá bán bất động sản chi tiết theo tỉnh thành, quận huyện và loại hình bất động sản. Dữ liệu tin cậy, cập nhật liên tục."
        />
        <meta property="og:title" content={pageTitle} />
        <link
          rel="canonical"
          href="https://giabatdongsan.info.vn/bieu-do-gia-ban"
        />
      </Helmet>
      <GoogleTag />
      <Header />
      <SharedRealEstateAnalytics
        pageTitle={pageTitle}
        unitText="(đơn vị: triệu VND/m2)"
        priceUnit="triệu/m2"
        realEstateTypes={realEstateTypesForSale}
        priceType="Bán"
      />
      <SEOTags />
      <Footer />
    </>
  );
}
